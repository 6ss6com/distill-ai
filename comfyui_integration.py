"""
DistillAI ↔ OpenClaw ComfyUI Integration Layer

将ComfyUI变成OpenClaw可对话的创意引擎。
通过自然语言聊天直接生成图片/视频/语音，
支持导入自定义ComfyUI工作流。

原理:
  OpenClaw (LLM对话) → DistillAI (人格+工具编排) → ComfyUI (本地生成)
                              ↓
                    persona_skills.py (图片生成)
                    voice_distiller.py (语音合成)
                    custom workflows (用户工作流)
"""

import requests, json, base64, io, os, time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from PIL import Image


# ============================================================
# ComfyUI Client
# ============================================================

class ComfyUIClient:
    """
    ComfyUI REST API客户端

    功能:
    - 图像生成 (文生图/图生图/ControlNet)
    - 视频生成 (SVD-XT/Animtatell)
    - 工作流执行
    - 自定义模板导入
    """

    def __init__(self, host: str = "localhost", port: int = 8188, username: str = None, password: str = None):
        self.base_url = f"http://{host}:{port}"
        self.auth = (username, password) if username else None
        self.session = requests.Session()
        if self.auth:
            self.session.auth = self.auth

    def is_alive(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/system_stats", timeout=5)
            return r.status_code == 200
        except:
            return False

    def get_history(self, prompt_id: str) -> dict:
        r = self.session.get(f"{self.base_url}/history/{prompt_id}", timeout=30)
        return r.json() if r.status_code == 200 else {}

    def get_image(self, filename: str) -> bytes:
        r = self.session.get(f"{self.base_url}/view", params={"filename": filename}, timeout=30)
        return r.content if r.status_code == 200 else b""

    def queue_prompt(self, workflow: dict) -> Tuple[str, str]:
        """
        执行工作流

        Returns: (prompt_id, prompt_hash)
        """
        payload = {"prompt": workflow, "last_node_id": None}
        r = self.session.post(f"{self.base_url}/prompt", json=payload, timeout=30)
        if r.status_code != 200:
            return "", ""
        data = r.json()
        return data.get("prompt_id", ""), data.get("number", "")

    def wait_for_result(self, prompt_id: str, timeout: int = 120) -> dict:
        """等待工作流完成"""
        start = time.time()
        while time.time() - start < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(2)
        return {}

    # ===== 预设工作流 =====

    def txt2img(self, prompt: str, model: str = "sd15", negative: str = "", steps: int = 20) -> List[bytes]:
        """
        文生图

        Args:
            prompt: 正向提示词
            negative: 负向提示词
            model: 模型名称
            steps: 采样步数
        """
        workflow = {
            "3": {"inputs": {"text": prompt, "clip": ["4", 0]}, "class_type": "CLIPTextEncode"},
            "4": {"inputs": {"text": negative, "clip": ["5", 0]}, "class_type": "CLIPTextEncode"},
            "6": {"inputs": {"samples": ["15", 0], "model": ["12", 0]}, "class_type": "KSampler"},
            "8": {"inputs": {"filename": "output.png", "type": "output"}, "class_type": "SaveImage"},
            "12": {"inputs": {"ckpt_name": model}, "class_type": "CheckpointLoaderSimple"},
            "15": {"inputs": {"seed": 0, "steps": steps, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "positive": ["3", 0], "negative": ["4", 0], "model": ["12", 0], "latent_image": ["16", 0]}, "class_type": "KSampler"},
            "16": {"inputs": {"width": 512, "height": 512, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        }
        prompt_id, _ = self.queue_prompt(workflow)
        if not prompt_id:
            return []

        result = self.wait_for_result(prompt_id)
        images = []
        for node_id, node_data in result.get("outputs", {}).items():
            if "images" in node_data:
                for img_info in node_data["images"]:
                    img_bytes = self.get_image(img_info["filename"])
                    if img_bytes:
                        images.append(img_bytes)
        return images

    def img2img(self, image_bytes: bytes, prompt: str, strength: float = 0.7) -> List[bytes]:
        """
        图生图
        """
        # 需要先上传图片获取hash
        files = {"image": ("input.png", image_bytes, "image/png")}
        r = self.session.post(f"{self.base_url}/upload/image", files=files, timeout=30)
        if r.status_code != 200:
            return []

        upload_result = r.json()
        image_name = upload_result.get("name", "")

        workflow = {
            "10": {"inputs": {"image": image_name}, "class_type": "LoadImage"},
            "3": {"inputs": {"text": prompt}, "class_type": "CLIPTextEncode"},
            "15": {"inputs": {"strength": strength}, "class_type": "WaltherDeNoiser"},
        }
        prompt_id, _ = self.queue_prompt(workflow)
        if not prompt_id:
            return []

        result = self.wait_for_result(prompt_id)
        images = []
        for node_id, node_data in result.get("outputs", {}).items():
            if "images" in node_data:
                for img_info in node_data["images"]:
                    img_bytes = self.get_image(img_info["filename"])
                    if img_bytes:
                        images.append(img_bytes)
        return images


# ============================================================
# OpenClaw ComfyUI Skill (chat-to-generate)
# ============================================================

class ComfyUIChatSkill:
    """
    OpenClaw对话生成技能

    用法:
        skill = ComfyUIChatSkill()
        result = skill.generate_image("画一只在月球上的猫")
        result = skill.generate_video("海边日落", model="svd-xt")
        result = skill.run_workflow("my_workflow.json", custom_params)
    """

    def __init__(self, comfyui_client: ComfyUIClient = None, default_model: str = "sd15"):
        self.client = comfyui_client or ComfyUIClient()
        self.default_model = default_model
        self.active_workflows = {}

    def is_available(self) -> bool:
        return self.client.is_alive()

    def generate_image(self, prompt: str, negative: str = "", model: str = None, size: Tuple[int,int] = (512,512)) -> Dict:
        """
        聊天生成图片

        集成到DistillAI persona skill系统
        """
        if not self.is_available():
            return {"error": "ComfyUI not reachable", "suggestion": "Start ComfyUI or check host/port"}

        model = model or self.default_model
        try:
            images = self.client.txt2img(prompt, model=model, negative=negative)
            if images:
                # 保存到本地
                output_dir = Path.home() / ".openclaw" / "workspace" / "distill-ai" / "outputs"
                output_dir.mkdir(parents=True, exist_ok=True)
                saved_paths = []
                for i, img_bytes in enumerate(images):
                    path = output_dir / f"img_{int(time.time())}_{i}.png"
                    with open(path, 'wb') as f:
                        f.write(img_bytes)
                    saved_paths.append(str(path))

                return {
                    "success": True,
                    "count": len(images),
                    "paths": saved_paths,
                    "prompt": prompt,
                    "model": model,
                }
            else:
                return {"error": "Generation failed, no images returned"}
        except Exception as e:
            return {"error": str(e)}

    def generate_video(self, prompt: str, model: str = "svd-xt", duration_frames: int = 61) -> Dict:
        """
        聊天生成视频 (ComfyUI SVD-XT / CogVideoX)

        ComfyUI工作流:
        SVD-XT: prompt → CLIP → VAE Encode → SVD Model → VAE Decode → Decode → Save
        """
        if not self.is_available():
            return {"error": "ComfyUI not reachable"}

        # 视频生成需要特定工作流
        workflow = self._build_video_workflow(prompt, model, duration_frames)
        prompt_id, _ = self.client.queue_prompt(workflow)
        if not prompt_id:
            return {"error": "Failed to queue video workflow"}

        result = self.client.wait_for_result(prompt_id, timeout=300)  # 视频生成可能需要5分钟

        videos = []
        for node_id, node_data in result.get("outputs", {}).items():
            if "videos" in node_data:
                for vid_info in node_data["videos"]:
                    videos.append(vid_info["filename"])

        return {
            "success": len(videos) > 0,
            "videos": videos,
            "prompt": prompt,
            "model": model,
        }

    def _build_video_workflow(self, prompt: str, model: str, frames: int) -> dict:
        """构建视频生成工作流"""
        if model == "cogvideo":
            return self._build_cogvideo_workflow(prompt, frames)
        else:
            return self._build_svd_workflow(prompt, frames)

    def _build_svd_workflow(self, prompt: str, frames: int) -> dict:
        """SVD-XT 工作流"""
        return {
            "3": {"inputs": {"text": prompt}, "class_type": "CLIPTextEncode"},
            "model_node": {
                "inputs": {
                    "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
                    "width": 1024, "height": 576, "video_frames": frames
                },
                "class_type": "SVD_img2vid"
            },
            "decode_node": {"inputs": {}, "class_type": "VAEDecode"},
            "output_node": {"inputs": {"filename": f"video_{int(time.time())}.mp4", "format": "video/mp4"}, "class_type": "EncodeVideo"},
        }

    def _build_cogvideo_workflow(self, prompt: str, frames: int) -> dict:
        """CogVideoX 工作流"""
        return {
            "3": {"inputs": {"text": prompt}, "class_type": "CLIPTextEncode"},
            "model_node": {
                "inputs": {
                    "model_name": "THUDM/CogVideoX-5b",
                    "width": 720, "height": 480, "frames": frames
                },
                "class_type": "CogVideoX"
            },
            "decode": {"inputs": {}, "class_type": "CogVideoX_Decode"},
            "output": {"inputs": {"filename": f"cog_{int(time.time())}.mp4"}, "class_type": "SaveVideo"},
        }

    def run_workflow(self, workflow_path: str = None, workflow_dict: dict = None, **params) -> Dict:
        """
        执行自定义工作流

        Args:
            workflow_path: .json工作流文件路径
            workflow_dict: 工作流dict (直接传入)
            **params: 覆盖参数
        """
        if not self.is_available():
            return {"error": "ComfyUI not reachable"}

        if workflow_path:
            with open(workflow_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)
        elif workflow_dict:
            workflow = workflow_dict
        else:
            return {"error": "No workflow provided"}

        # 注入参数
        for key, value in params.items():
            for node_id in workflow:
                if key in workflow[node_id].get("inputs", {}):
                    workflow[node_id]["inputs"][key] = value

        prompt_id, _ = self.client.queue_prompt(workflow)
        if not prompt_id:
            return {"error": "Failed to queue workflow"}

        result = self.client.wait_for_result(prompt_id)

        outputs = {}
        for node_id, node_data in result.get("outputs", {}).items():
            if "images" in node_data:
                outputs[node_id] = [img["filename"] for img in node_data["images"]]
            elif "videos" in node_data:
                outputs[node_id] = [vid["filename"] for vid in node_data["videos"]]

        return {
            "success": bool(outputs),
            "prompt_id": prompt_id,
            "outputs": outputs,
        }

    def list_workflows(self) -> List[str]:
        """列出已保存的工作流"""
        workflow_dir = Path.home() / ".openclaw" / "workspace" / "distill-ai" / "workflows"
        if not workflow_dir.exists():
            return []
        return [f.name for f in workflow_dir.glob("*.json")]

    def import_workflow(self, workflow_json: dict, name: str) -> str:
        """导入自定义工作流"""
        workflow_dir = Path.home() / ".openclaw" / "workspace" / "distill-ai" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r'[^\w\-]', '_', name)
        path = workflow_dir / f"{safe_name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(workflow_json, f, ensure_ascii=False, indent=2)
        return str(path)


# ===== OpenClaw Tool Registration Format =====

COMFYUI_TOOL_SCHEMA = {
    "name": "comfyui_generate",
    "description": """Generate images, videos, and audio via ComfyUI from natural language.
Supports custom workflow import. Uses local GPU for fast generation.

Available actions:
- generate_image: Text-to-image (SD 1.5/SDXL/Flux)
- generate_video: Text-to-video (SVD-XT, CogVideoX)
- run_workflow: Execute saved or imported ComfyUI workflows
- import_workflow: Load custom workflow JSON""",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["generate_image", "generate_video", "run_workflow", "list_workflows", "import_workflow"]
            },
            "prompt": {"type": "string", "description": "Generation prompt"},
            "negative": {"type": "string", "description": "Negative prompt (images only)"},
            "model": {"type": "string", "description": "Model name (default: sd15)"},
            "workflow_name": {"type": "string", "description": "Workflow name for run/import"},
            "workflow_json": {"type": "object", "description": "Workflow JSON for import"},
        },
        "required": ["action"]
    }
}


# ===== Integration with DistillAI Persona Skills =====

def comfyui_persona_skill(persona: str, prompt: str, action: str = "generate_image") -> str:
    """
    ComfyUI集成到DistillAI人格技能系统

    用法 (在persona_skills.py中):
        from comfyui_integration import comfyui_persona_skill

        result = comfyui_persona_skill("沙雕网友", "画个表情包", "generate_image")
    """
    skill = ComfyUIChatSkill()

    # 聊天语气转换
    persona_tones = {
        "沙雕网友": {"style": "搞笑", "add_prompt": "meme style, cartoon"},
        "巴菲特": {"style": "专业", "add_prompt": "professional, clean"},
        "占星师": {"style": "神秘", "add_prompt": "mystical, ethereal"},
        "苍炎剑士": {"style": "战斗", "add_prompt": "fantasy, epic, dynamic"},
        "九尾灵狐": {"style": "唯美", "add_prompt": "beautiful, elegant"},
    }

    tone = persona_tones.get(persona, {"style": "normal", "add_prompt": ""})
    enhanced_prompt = f"{prompt}, {tone['add_prompt']}" if tone['add_prompt'] else prompt

    if action == "generate_image":
        result = skill.generate_image(enhanced_prompt)
        if result.get("success"):
            paths = result.get("paths", [])
            return f"[{persona}] 图片生成完成! 共{len(paths)}张，保存在: {', '.join(paths[:2])}"
        else:
            return f"[{persona}] 图片生成失败: {result.get('error', 'unknown error')}"

    elif action == "generate_video":
        result = skill.generate_video(enhanced_prompt)
        if result.get("success"):
            return f"[{persona}] 视频生成完成! 文件: {result.get('videos', [])[0]}"
        else:
            return f"[{persona}] 视频生成失败: {result.get('error', 'unknown error')}"

    return f"[{persona}] ComfyUI action '{action}' completed"


# ===== 快速测试 =====

if __name__ == "__main__":
    print("=== ComfyUI Chat Skill ===")

    skill = ComfyUIChatSkill()
    print("ComfyUI alive:", skill.is_available())
    print("Available workflows:", skill.list_workflows())

    # 测试图像生成(如果ComfyUI在运行)
    result = skill.generate_image("a cute cat in space, digital art")
    print("Image result:", result.get("success"), "| Count:", result.get("count", 0))

    print()
    print("Tool schema:")
    print(json.dumps(COMFYUI_TOOL_SCHEMA["description"][:200], ensure_ascii=False))