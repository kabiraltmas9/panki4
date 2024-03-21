#!/usr/bin/env python3

"""
A flash utility script to flash crazyflies with the latest firmware

    2024 - K. N. McGuire (Bitcraze AB)
"""

import rclpy
from rclpy.node import Node
import cflib.crtp  # noqa
from cflib.bootloader import Bootloader, Target
from cflib.bootloader.boottypes import BootVersion
import argparse

class Flash(Node):
    def __init__(self, uri, file_name, target):
        super().__init__('flash')
    
        self.get_logger().info(f"Flashing {uri} with {file_name} for {target}")

        targets = []
        if target == "all":
            targets = []
            if file_name.endswith(".bin"):
                self.get_logger().info("Need a .zip file for all targets")
                return
            else:
                targets = []
        elif target.startswith("cf2"):
            if file_name.endswith(".bin") and file_name.startswith("cf2"):
                [target, type] = target.split("-")
                targets.append(Target("cf2", 'stm32', 'fw', [], []))
            else:
                self.get_logger().error(f"Need cf2*.bin file for target {target}")
                return
        else:
            self.get_logger().error(f"Unknown target: {target}")
            return

        print(targets)
        bl = Bootloader(uri)
        try:
            bl.flash_full(None, file_name, True, targets)

        except Exception as e:
            self.get_logger().error(f"Failed to flash, Error {str(e)}")
        finally:
            if bl:
                bl.close()

        return

def main(args=None):
    cflib.crtp.init_drivers()
    rclpy.init(args=args)
    parser = argparse.ArgumentParser(description="This is a sample script")
    parser.add_argument('--uri', type=str, default="radio://0/80/2M/E7E7E7E7E7", help='unique resource identifier')
    parser.add_argument('--file_name', type=str, default="firmware", help='')
    parser.add_argument('--target', type=str, default="all", help='')

    # Parse the arguments
    args = parser.parse_args()

    print("URI: ", args.uri)
    flash_node = Flash(args.uri, args.file_name, args.target)

    flash_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()