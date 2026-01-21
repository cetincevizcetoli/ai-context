from setuptools import setup

setup(
    name="ai-context",
    version="1.0.0",
    py_modules=["ai_context"],
    install_ Harris=[], # Harici kütüphane gerekmiyor
    entry_points={
        'console_scripts': [
            'ai-context=ai_context:main',
        ],
    },
)