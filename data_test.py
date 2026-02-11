import os
import time

def single_test(target_path, size_mb=50):
    """Runs one write/read test and returns speeds."""
    result = {"write": None, "read": None, "error": None}

    try:
        data = os.urandom(size_mb * 1024 * 1024)
        temp_file = os.path.join(target_path, "softcable_test.bin")

        # WRITE TEST
        start = time.time()
        with open(temp_file, "wb") as f:
            f.write(data)
        end = time.time()
        result["write"] = round(size_mb / (end - start), 2)

        # READ TEST
        start = time.time()
        with open(temp_file, "rb") as f:
            f.read()
        end = time.time()
        result["read"] = round(size_mb / (end - start), 2)

        os.remove(temp_file)

    except Exception as e:
        result["error"] = str(e)

    return result


def run_speed_test(target_path):
    """Runs 4 tests and returns individual + average results."""
    results = []
    write_speeds = []
    read_speeds = []

    for i in range(4):
        test = single_test(target_path)
        results.append(test)

        if test["error"]:
            return {"error": test["error"]}

        write_speeds.append(test["write"])
        read_speeds.append(test["read"])

    avg_write = round(sum(write_speeds) / 4, 2)
    avg_read = round(sum(read_speeds) / 4, 2)

    return {
        "error": None,
        "runs": results,
        "avg_write": avg_write,
        "avg_read": avg_read
    }
