import cv2
import os
import numpy as np
from PIL import Image

from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url
from realesrgan import RealESRGANer
from gfpgan import GFPGANer

class RealESRGANProcessor:
    def __init__(self, model_name='RealESRGAN_x4plus', face_enhance=True, fp32=False, gpu_id=None):
        self.model_name = model_name
        self.face_enhance = face_enhance
        self.fp32 = fp32
        self.gpu_id = gpu_id
        
        # Initialize the upsampler
        self.upsampler = self._initialize_upsampler()
        
        # Initialize face enhancer if needed
        self.face_enhancer = None
        if self.face_enhance:
            self._initialize_face_enhancer()

    def _initialize_upsampler(self):
        """Initialize the Real-ESRGAN upsampler"""
        model_name = self.model_name.split('.')[0]

        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']

        # Determine model path
        model_path = os.path.join('weights', model_name + '.pth')
        if not os.path.isfile(model_path):
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            for url in file_url:
                model_path = load_file_from_url(
                    url=url, model_dir=os.path.join(ROOT_DIR, 'weights'), progress=True, file_name=None)

        # Create upsampler
        upsampler = RealESRGANer(
            scale=netscale,
            model_path=model_path,
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=not self.fp32,
            gpu_id=self.gpu_id)
            
        return upsampler

    def _initialize_face_enhancer(self):
        """Initialize GFPGAN face enhancer"""
        self.face_enhancer = GFPGANer(
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
            upscale=4,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=self.upsampler)

    def enhance_image(self, image, outscale=4):
        """Enhance a single image (PIL Image or numpy array)"""
        # Convert PIL Image to numpy array (OpenCV format)
        if isinstance(image, Image.Image):
            # Convert RGB to BGR for OpenCV
            img_array = np.array(image)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_array = image

        try:
            if self.face_enhance and self.face_enhancer:
                # Use GFPGAN for face enhancement
                _, _, output = self.face_enhancer.enhance(
                    img_array, 
                    has_aligned=False, 
                    only_center_face=False, 
                    paste_back=True
                )
            else:
                # Use Real-ESRGAN only
                output, _ = self.upsampler.enhance(img_array, outscale=outscale)
                
            # Convert back to RGB
            output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            return Image.fromarray(output_rgb)
            
        except RuntimeError as error:
            print('Error during enhancement:', error)
            raise

    def enhance_image_file(self, input_path, output_path, outscale=4):
        """Enhance an image file and save to output path"""
        # Read image
        img = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Could not read image from {input_path}")

        # Enhance image
        enhanced_img = self.enhance_image(img, outscale=outscale)
        
        # Save enhanced image
        enhanced_img.save(output_path)
        return output_path
    