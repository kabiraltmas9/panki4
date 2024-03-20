#!/usr/bin/env python3

"""
A flash utility script to flash crazyflies with the latest firmware

    2024 - K. N. McGuire (Bitcraze AB)
"""

import rclpy
from rclpy.node import Node
from cflib.bootloader import Bootloader, Target
from cflib.bootloader.boottypes import BootVersion

class Flash(Node):
    def __init__(self):
        super().__init__('flash')
    
        self.get_logger().info(f"Flash node has started")

        self.declare_parameter('uri', 'radio://0/80/2M/E7E7E7E7E7')
        self.declare_parameter('file_name', 'cf2.bin')
        self.declare_parameter('target', 'all')


        uri = self.get_parameter('uri').value
        file_name = self.get_parameter('file_name').value
        target = self.get_parameter('target').value

        self.get_logger().info(f"Flashing {uri} with {file_name} for {target}")

        bl = Bootloader(uri)

        bl.flash_full(None, file_name, True, None)


def main(args=None):
    rclpy.init(args=args)

    flash_node = Flash()

    rclpy.spin(flash_node)

    flash_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()