from setuptools import setup, find_packages

setup(
    name="distill-ai",
    version="2.5.0",
    description="AI Persona Platform - DistillAI 钛格栅AI人格平台",
    author="DistillAI",
    author_email="distillai@github.com",
    url="https://github.com/6ss6com/distill-ai",
    packages=find_packages(),
    install_requires=[
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "requests>=2.31.0",
    ],
    python_requires=">=3.10",
)