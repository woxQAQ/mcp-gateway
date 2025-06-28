from oas.conv import OpenAPIConverter


def main():
    print("Hello from myunla!")


if __name__ == "__main__":
    conv = OpenAPIConverter("oas/petstore.v3.yaml")
    print(conv.spec["paths"])
    for path, path_item in conv.spec["paths"].items():
        for method, operation in path_item.items():
            print(path, method, operation)
