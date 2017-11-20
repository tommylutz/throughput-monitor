#!/usr/bin/python3
import grpc
import tpmon_pb2
import tpmon_pb2_grpc
from pprint import pprint
import argparse

def run():
        parser = argparse.ArgumentParser(description='Move the silly needle')
        parser.add_argument('-a', '--addr', metavar='ADDR', default='localhost:5200', help='Address (including port) where the throughput monitor server is running')
        parser.add_argument('-p', '--pos', metavar='P', type=int, default=0, help='Position to move the needle (0 is lowest, approx 1310 is highest)')
        args = parser.parse_args()

        channel = grpc.insecure_channel(args.addr)
        stub = tpmon_pb2_grpc.ThroughputRendererStub(channel)
        response = stub.QueryPosition(tpmon_pb2.QueryPositionRequest())
        print("Position %s of %s\n"%(response.raw_position, response.max_raw_position))

        response = stub.SetPosition(tpmon_pb2.SetPositionRequest(raw_position=args.pos))
        print("Response to setting position: %s"%(repr(response)))

if __name__ == '__main__':
    run()
