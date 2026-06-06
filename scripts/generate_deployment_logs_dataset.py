from dataset_factory import parse_output_dir, print_written, write_deployment_logs


if __name__ == "__main__":
    output_dir = parse_output_dir()
    print_written([write_deployment_logs(output_dir)])
