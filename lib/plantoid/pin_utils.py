import os
from dotenv import load_dotenv
from pinata import Pinata

from escpos.printer import Usb
import qrcode
from PIL import Image


load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_SECRET_KEY")
PINATA_JWT = os.environ.get('PINATA_JWT')




def create_ipfs_qr(ipfs_link, output_file="/tmp/ipfs_qrcode.png", size=10):
    """
    Convert an IPFS link to a QR code and save it as an image file.
    
    Parameters:
    - ipfs_link (str): The IPFS link/CID to encode in the QR code
    - output_file (str): Filename for the output QR code image
    - size (int): Size of the QR code (higher = larger image)
    
    Returns:
    - str: Path to the saved QR code image file
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=4,
    )
    
    # Add the IPFS link data
    qr.add_data(ipfs_link)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    img.save(output_file)
    
    return os.path.abspath(output_file)



def print_thermal_txt(textual):

    try: 
        p = Usb(0x0416, 0x5011, in_ep=0x81, out_ep=0x01)
        p.text(textual)
        p.cut()
        p.close()
    except Exception as e:
        print(f"Error: Thermal printer not connected or accessible - {e}")
        return False
    return True


def print_thermal_img(image_file):
    
    try:
        p = Usb(0x0416, 0x5011, in_ep=0x81, out_ep=0x01)

        img = Image.open(image_file)
        img = img.resize((400, 400))

        p.image(img)
        p.cut()
        p.close()
    
    except Exception as e:
        print(f"Error: Thermal printer not connected or accessible - {e}")
        return False
    return True
