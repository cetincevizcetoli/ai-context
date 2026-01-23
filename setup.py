from setuptools import setup

setup(
    name="ai-context",
    version="1.0.0",
    py_modules=["ai_context"], # Dosya adın ai_context.py olmalı
    install_requires=[],        # 'install_ Harris' kısmını düzelttik
    entry_points={
        'console_scripts': [
            'ai-context=ai_context:main',
        ],
    },
)
