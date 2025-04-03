from pinata import Pinata
from dotenv import load_dotenv
import os

from escpos.printer import Usb
import qrcode
from PIL import Image

def pin_metadata_to_ipfs(path):
    pinata = Pinata(PINATA_API_KEY, PINATA_API_SECRET, PINATA_JWT)
    print("file to pin is: ", path)
    print("API KEY = ", PINATA_API_KEY)
    print("SECRET = ", PINATA_API_SECRET)
    print("JWT = ", PINATA_JWT)

    response = pinata.pin_file(path)
    print("ppinata response = ", response)

    is_duplicate = False

    if response and response.get('data'):

        pinned = response['data']['IpfsHash']
        print("pinned to ... ", pinned);

        if (response['data'].get('isDuplicate')) is not None:
            is_duplicate = True
            print("It is duplicate")
    return pinned



def create_ipfs_qr(ipfs_link, output_file="ipfs_qrcode.png", size=10):
    """
    Convert an IPFS link to a QR code and save it as an image file.
    
    Parameters:
    - ipfs_link (str): The IPFS link/CID to encode in the QR code
    - output_file (str): Filename for the output QR code image
    - size (int): Size of the QR code (higher = larger image)
    
    Return
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



def print_thermal(image_file):

    p = Usb(0x0416, 0x5011, in_ep=0x81, out_ep=0x03)

    img = Image.open(image_file)
    img = img.resize((400, 400))

    p.image(img)
    p.cut()



load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_SECRET_KEY")
PINATA_JWT = os.environ.get("PINATA_JWT")

ipfs_link = pin_metadata_to_ipfs("./sys.py")
ipfs_link = "https://ipfs.io/ipfs/" + ipfs_link
print("IPFS link = ", ipfs_link)

qrcode = create_ipfs_qr(ipfs_link, output_file="ipfs_qrcode.png", size=10)

print_thermal(qrcode)
