import usb.core
import usb.util

# Find the printer
dev = usb.core.find(idVendor=0x0416, idProduct=0x5011)

if dev is None:
    print("Printer not found!")
else:
    print(f"Found printer: {dev}")
    
    # Set configuration
    try:
        dev.set_configuration()
    except:
        pass  # May already be configured
    
    # Get the configuration
    cfg = dev.get_active_configuration()
    
    # Find the interface
    intf = cfg[(0,0)]
    
    # List all endpoints
    print("\nEndpoints found:")
    for ep in intf:
        print(f"Endpoint Address: 0x{ep.bEndpointAddress:02x}")
        print(f"  Direction: {'IN' if ep.bEndpointAddress & 0x80 else 'OUT'}")
        print(f"  Type: {ep.bmAttributes & 0x03}")
        print()
