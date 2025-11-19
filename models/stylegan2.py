import torch
import numpy as np
from PIL import Image
import io
import sys
import os
from typing import List, Optional

# Path to submodule
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
original_repo_path = os.path.join(project_root, "stylegan2-ada-pytorch")
sys.path.insert(0, original_repo_path)

try:
    import dnnlib
    import legacy
except ImportError as e:
    raise ImportError(f"Could not import StyleGAN2 module: {e}")

class StyleGAN2Generator:
    def __init__(self, network_pkl: str):
        self.network_pkl = network_pkl
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.G = self._load_network()
    
    def _load_network(self):
        """Load network using the exact same code as generate.py"""
        print(f'Loading networks from "{self.network_pkl}"...')
        with dnnlib.util.open_url(self.network_pkl) as f:
            G = legacy.load_network_pkl(f)['G_ema'].to(self.device)
        
        if not torch.cuda.is_available():
            G.apply(lambda module: setattr(module, 'use_fp16', False))
        return G
    
    def generate_from_seed(
        self, 
        seed: int, 
        truncation_psi: float = 0.5,
        noise_mode: str = 'const',
        class_idx: Optional[int] = None
    ) -> Image.Image:
        """Generate image using the exact same logic as generate.py"""
        
        # Labels
        label = torch.zeros([1, self.G.c_dim], device=self.device)
        if self.G.c_dim != 0 and class_idx is not None:
            label[:, class_idx] = 1
        
        # Generate latent vector
        z = torch.from_numpy(np.random.RandomState(seed).randn(1, self.G.z_dim)).to(self.device)
        
        # Generate image
        print('Generating single face ...')
        with torch.no_grad():
            img = self.G(z, label, truncation_psi=truncation_psi, noise_mode=noise_mode)
            img = (img.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
        
        # Convert to PIL Image
        img_np = img[0].cpu().numpy()
        return Image.fromarray(img_np, 'RGB')
    
    def generate_from_grid(
            self,
            row_seeds: List[int],
            col_seeds: List[int],
            col_styles: List[int] = None,
            truncation_psi: float = 0.5,
            noise_mode: str = 'const'
    ) -> Image.Image:
        """Generate style mixing grid image"""

        if col_styles is None:
            col_styles = list(range(0, 7))

        all_seeds = list(set(row_seeds + col_seeds))
        all_z = np.stack([np.random.RandomState(seed).randn(self.G.z_dim) for seed in all_seeds])
        all_w = self.G.mapping(torch.from_numpy(all_z).to(self.device), None)
        w_avg = self.G.mapping.w_avg
        all_w = w_avg + (all_w - w_avg) * truncation_psi
        w_dict = {seed: w for seed, w in zip(all_seeds, list(all_w))}

        all_images = self.G.synthesis(all_w, noise_mode=noise_mode)
        all_images = (all_images.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8).cpu().numpy()
        image_dict = {(seed, seed): image for seed, image in zip(all_seeds, list(all_images))}

        print('Generating style-mixed images...')
        for row_seed in row_seeds:
            for col_seed in col_seeds:
                w = w_dict[row_seed].clone()
                w[col_styles] = w_dict[col_seed][col_styles]
                image = self.G.synthesis(w[np.newaxis], noise_mode=noise_mode)
                image = (image.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
                image_dict[(row_seed, col_seed)] = image[0].cpu().numpy()

        print('Creating style mix grid...')
        W = self.G.img_resolution
        H = self.G.img_resolution
        canvas = Image.new('RGB', (W * (len(col_seeds) + 1), H * (len(row_seeds) + 1)), 'black')
        
        for row_idx, row_seed in enumerate([0] + row_seeds):
            for col_idx, col_seed in enumerate([0] + col_seeds):
                if row_idx == 0 and col_idx == 0:
                    continue
                key = (row_seed, col_seed)
                if row_idx == 0:
                    key = (col_seed, col_seed)
                if col_idx == 0:
                    key = (row_seed, row_seed)
                
                # Get the image and paste it onto the canvas
                img_array = image_dict[key]
                img_pil = Image.fromarray(img_array, 'RGB')
                canvas.paste(img_pil, (W * col_idx, H * row_idx))
        
        return canvas
        
    
    def image_to_bytes(self, image: Image.Image, format: str = "PNG") -> bytes:
        """Convert PIL image to bytes for API response"""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=format)
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()
    
    def get_network_info(self) -> dict:
        """Get information about the loaded network"""
        return {
            'resolution': self.G.img_resolution,
            'mapping_layers': self.G.mapping.num_layers,
            'synthesis_layers': self.G.synthesis.num_layers,
            'latent_dim': self.G.z_dim,
            'conditioning_dim': self.G.c_dim,
            'device': str(self.device)
        }
    