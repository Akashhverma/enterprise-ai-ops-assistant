from dataset_factory import parse_output_dir, print_written, write_all


if __name__ == "__main__":
    output_dir = parse_output_dir()
    print_written(write_all(output_dir))
