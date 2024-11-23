from setuptools import setup, find_packages

setup(
    name="InteractiveChatApp",
    version="1.0.0",
    description="An interactive chatbot with emotion classification and backend Flask integration",
    author="Your Name",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "transformers",
        "nltk",
        "openai",
        "python-dotenv",
        "speechrecognition",
        "keyboard",
        "pygame",
        "requests",
        "flask",
        "flask-socketio",
        "flask-cors",
        "langchain",
        "g4f",  # Update or verify compatibility for your environment
        "tensorflow",
        "torch",  # Adjust CUDA version based on your system
        "torchaudio",
        "elevenlabs",
        "coqui-tts",
        "pywebview",
        "screeninfo",
        "tqdm",
        "tf-keras",
        "langchain_ollama",
        "groq",
    ],
    entry_points={
        "console_scripts": [
            "start_chat=main:interactive_chat",
            "start_server=backflask:app.run",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.10",
)
