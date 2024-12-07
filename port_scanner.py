import asyncio
import time
from socket import *

semaphore = asyncio.Semaphore(500)  # Limit concurrent tasks
open_ports = []  # List to store open ports and services

def is_host_reachable(target_IP):
    """Check if the host is reachable by attempting a connection."""
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.settimeout(1)  # Set a short timeout
            s.connect((target_IP, 80))  # Attempt to connect to port 80
        return True
    except (OSError, ConnectionRefusedError):
        return False

async def scan_port(target_IP, port):
    """Asynchronously scan a single port and retrieve service name if open."""
    async with semaphore:
        try:
            # Attempt to establish a connection
            await asyncio.wait_for(asyncio.open_connection(target_IP, port), timeout=0.5)
            try:
                # Get the service name if available
                service_name = getservbyport(port)
            except OSError:
                service_name = "Unknown Service"
            
            print(f"Port {port}: OPEN (Service: {service_name})")
            open_ports.append((port, service_name))
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            pass  # Port is closed or not responding
        except Exception as e:
            print(f"Error scanning port {port}: {e}")


async def scan_ports_concurrently(target_IP, start_port, end_port):
    """Scan ports concurrently using asyncio tasks."""
    tasks = [
        scan_port(target_IP, port)
        for port in range(start_port, end_port + 1)
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        target = input("Enter host for scanning: ")
        target_IP = gethostbyname(target)
        print(f"Start scanning on host: {target_IP}")

        if not is_host_reachable(target_IP):
            print(f"Error: The host {target_IP} is not reachable. Please check the target and try again.")
            exit()

        print(f"Host {target_IP} is reachable. Starting port scan.")

        start_port = int(input("Enter the start port: "))
        end_port = int(input("Enter the end port: "))
        if start_port < 1 or end_port > 65535 or start_port > end_port:
            print("Invalid port range. Please enter a valid range (1-65535).")
            exit()

        start_time = time.time()
        # Use the current event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(scan_ports_concurrently(target_IP, start_port, end_port))
        print('Time taken: ', time.time() - start_time)

        if open_ports:
            print("Open ports and their services:")
            for port, service in open_ports:
                print(f"Port {port}: {service}")
        else:
            print("No open ports found.")

    except gaierror:
        print("Error: Unable to resolve hostname. Please check the input.")
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
    except ValueError:
        print("Error: Invalid input. Please enter numeric values for ports.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
