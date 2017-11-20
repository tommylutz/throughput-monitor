pb_srcs = tpmon_pb2_grpc.py tpmon_pb2.py

all: tpmon.py $(pb_srcs)

$(pb_srcs): tpmon.proto
	python3 -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=. ./tpmon.proto

clean:
	rm $(pb_srcs)



