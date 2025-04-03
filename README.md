# 🧠 AutoMesh: Text-to-3D Mesh Generation

**AutoMesh** is a deep learning framework for generating 3D meshes from natural language prompts. It leverages transformer-based text encoders, graph neural networks (GNNs), and vector quantization (VQ) to reconstruct 3D mesh structures in graph form. The system supports full preprocessing and real-time interaction via a Blender extension.

## 🔧 Key Features

- 🧾 **Text-conditioned mesh generation** using Transformer/LSTM models
- 🔁 **Graph-based decoding** to predict node positions and mesh connectivity
- ⚙️ **Blender-integrated preprocessing**: cleaning, merging, reducing vertices
- 📚 **Modular PyTorch pipeline**: Text Encoder, GNN, Feature Fusion, VQ, Decoder
- 📦 **Export support** for standard formats like `.json`, `.obj`, `.gltf`

## 🖼️ Applications

- Procedural 3D model generation
- AI-assisted design tools
- Data-driven mesh reconstruction
- 3D captioning and inverse tasks

> 🚀 Built for scalability, research flexibility, and seamless integration with Blender.

