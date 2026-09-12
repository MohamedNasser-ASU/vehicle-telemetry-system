import argparse
import re
import csv
import json
import statistics

def main():

    # command line arguments
    parser = argparse.ArgumentParser(description='Vehicle Telemetry Log Analyzer')
    parser.add_argument("path")
    parser.add_argument('--stats', action="store_true", help="show stats only")
    parser.add_argument('--events', action="store_true", help="show events only")
    parser.add_argument('--malformed', action="store_true", help="show malformed lines only")
    parser.add_argument('--csv', help="export telemetry to csv file")
    parser.add_argument('--json', help="export report to json file")

    args = parser.parse_args()

    # Load log file
    records, malformed = load_log(args.path)
    # get stats and events
    stats = analyze_records(records)
    events = log_events(records)

    summary = {
        "file": f"{args.path}",
        "duration": f"{records[-1]["timestamp"]/60000:.2f} minutes",
        "samples": len(records) + len(malformed),
        "valid_lines": len(records),
        "malformed_lines": len(malformed),
        "stats": stats,
        "events": events,
        "malformed": malformed,
    }

    if (args.csv):
        export_csv(records, args.csv)
        parser.exit(f"Data exported to {args.csv} succesfully!")
    if (args.json):
        export_json(summary, args.json)
        parser.exit(f"Data exported to {args.json} succesfully!")
    print()
    if ( args.stats ):
        format_stats(summary)
    elif ( args.events ):
        format_events(summary)
    elif ( args.malformed ):
        format_malformed(summary)
    else:
        format_report(summary)






def load_log(path):
    records   = []
    malformed = []
    with open(path) as file:
        for line_number, line in enumerate(file, start=1):
            record, state, reason = parse_record(line)
            if state == "ok":
                records.append(record)
            else:
                malformed.append((line_number, reason))

        return records, malformed

def parse_record(line):

    state = "ok"
    reason = ""
    # regex to validate log line
    if matches := re.search(r"^(\d+)\s+(INFO|WARN|ERROR)\s+(.+)$",line):

        # capture stuff
        timestamp = matches.group(1)
        level = matches.group(2)
        string = matches.group(3).strip()

        fields = []
        fields = string.split()
        # print(fields)
        record = {}
        record = {"timestamp": timestamp, "level": level }

        # form the dict
        for field in fields:

            try:
                # check for missing value
                if "=" not in field:
                    raise ValueError
                key, value = field.split("=",1)

                # check for duplicate keys
                if key.lower() not in record.keys():
                    record[key.lower()] = value
                else:
                    state = "malformed"
                    reason = "duplicate fields"

            except ValueError:
                state = "malformed"
                reason = "Missing '='"

        # no missing info validation
        info = ["temp_c", "supply_v", "rpm_l", "rpm_r", "cmd_l", "cmd_r", "throttle", "steer"]
        if level == "INFO" and "event" not in record and not all(key in record for key in info):
            state = "malformed"
            reason = "Missing telemetry"

        if level != "INFO" and ("event" not in record.keys()):
            state = "malformed"
            reason = "False Warning/Error"

        if state != "malformed":
            # type conversion
            INT_FIELDS = [
                "timestamp",
                "rpm_l",
                "rpm_r",
                "cmd_l",
                "cmd_r",
                "throttle",
                "steer",
                "ppr",
                "wheel_mm"
            ]
            FLOAT_FIELDS = [
                "temp_c",
                "supply_v",
                "nominal_v"
            ]
            for key, value in record.items():
                try:
                    if key in INT_FIELDS:
                        record[key] = int(value)

                    elif key in FLOAT_FIELDS:
                        record[key] = float(value)
                except ValueError:
                    state = "malformed"
                    reason = "Invalid value"

    else:
        # if didnt match regex
        state = "malformed"
        reason = "Invalid log line format"
        #print(state, reason)
        return None, state, reason

    #print(record, state, reason)
    return record, state, reason


def analyze_records(records):

    temps = []
    volts = []
    rpmr  = []
    rpml  = []
    cmdr  = []
    cmdl  = []
    throttle = []
    steer = []
    velocities = []
    telemetry = ["temp_c", "supply_v", "rpm_l", "rpm_r", "cmd_l", "cmd_r", "throttle", "steer"]
    wheel_mm = records[0]["wheel_mm"]

    for i in range(len(records)):
        if all(key in records[i] for key in telemetry) :
            temps.append(records[i]["temp_c"])
            volts.append(records[i]["supply_v"])
            rpml.append(records[i]["rpm_l"])
            rpmr.append(records[i]["rpm_r"])
            cmdl.append(records[i]["cmd_l"])
            cmdr.append(records[i]["cmd_r"])
            throttle.append(records[i]["throttle"])
            steer.append(records[i]["steer"])
            rpm_avg = statistics.mean((records[i]["rpm_l"],records[i]["rpm_r"]))
            diameter_m = wheel_mm / 1000
            circumference = 3.14159 * diameter_m
            velocity = rpm_avg * circumference * 60 / 1000
            velocities.append(velocity)

    stats = {
    "temps": get_stats(temps),
    "volts": get_stats(volts),
    "rpmr": get_stats(rpmr),
    "rpml": get_stats(rpml),
    "cmdr": get_stats(cmdr),
    "cmdl": get_stats(cmdl),
    "throttle": get_stats(throttle),
    "steer": get_stats(steer),
    "velocity": get_stats(velocities),
    "average_throttle":statistics.mean(abs(value) for value in throttle),
    "steering_activity": statistics.mean(abs(value) for value in steer)
    }
    return stats

def get_stats(values):
    return min(values), max(values), statistics.mean(values)

def log_events(records):

    events = {
        "warnings": 0,
        "errors": 0,
        "high_temperature": 0,
        "low_supply": 0,
        "motor_mismatch": 0,
        "motor_stall": 0
    }

    for record in records:
        if "event" in record:

            if record["level"] == "ERROR":
                events["errors"] += 1
            elif record["level"] == "WARN":
                events["warnings"] += 1
            if record["event"] == "HIGH_TEMPERATURE":
                events["high_temperature"] += 1
            elif record["event"] == "LOW_SUPPLY":
                events["low_supply"] += 1
            elif record["event"] == "MOTOR_SPEED_MISMATCH":
                events["motor_mismatch"] += 1
            elif record["event"] == "MOTOR_STALL":
                events["motor_stall"] += 1
        else:
            anomalies = detect_anomalies(record)
            # if anomaly is x and x is in events , events++
            for anomaly in anomalies:
                if anomaly == "high_temperature":
                    events["high_temperature"] += 1
                    events["warnings"] += 1
                elif anomaly == "low_supply":
                    events["low_supply"] += 1
                    events["warnings"] += 1
                elif anomaly == "motor_mismatch":
                    events["motor_mismatch"] += 1
                    events["warnings"] += 1
                elif anomaly == "motor_stall":
                    events["motor_stall"] += 1
                    events["errors"] += 1

    return events

def detect_anomalies(record):
    anomalies = []

    # log anomalies
    if record["temp_c"] >= 80:
        anomalies.append("high_temperature")
    if record["supply_v"] < 5.4:
        anomalies.append("low_supply")
    if record["rpm_r"] < 10 and abs(record["cmd_r"]) > 40 or record["rpm_l"] < 10 and abs(record["cmd_l"]) > 40:
        anomalies.append("motor_stall")
    if (abs(record["cmd_l"]) >= 40 and abs(record["cmd_r"]) >= 40 and abs(abs(record["cmd_l"]) - abs(record["cmd_r"])) <= 10) and record["cmd_l"] * record["cmd_r"] > 0:
        if abs(abs(record["rpm_r"]) - abs(record["rpm_l"])) >= 20:
            anomalies.append("motor_mismatch")
    return anomalies



def format_stats(summary):
    print("TEMPERATURE\n-----------")
    print(f"Minimum:\t\t{summary["stats"]["temps"][0]} °C")
    print(f"Maximum:\t\t{summary["stats"]["temps"][1]} °C")
    print(f"Average:\t\t{summary["stats"]["temps"][2]:.2f} °C\n")

    print("SUPPLY\n------")
    print(f"Minimum:\t\t{summary["stats"]["volts"][0]} Volts")
    print(f"Maximum:\t\t{summary["stats"]["volts"][1]} Volts")
    print(f"Average:\t\t{summary["stats"]["volts"][2]:.2f} Volts\n")

    print("LEFT MOTOR\n----------")
    print(f"Minimum RPM:\t\t{summary["stats"]["rpml"][0]}")
    print(f"Maximum RPM:\t\t{summary["stats"]["rpml"][1]}")
    print(f"Average RPM:\t\t{summary["stats"]["rpml"][2]:.2f}")
    print(f"Minimum CMD:\t\t{summary["stats"]["cmdl"][0]}")
    print(f"Maximum CMD:\t\t{summary["stats"]["cmdl"][1]}\n")

    print("RIGHT MOTOR\n-----------")
    print(f"Minimum RPM:\t\t{summary["stats"]["rpmr"][0]}")
    print(f"Maximum RPM:\t\t{summary["stats"]["rpmr"][1]}")
    print(f"Average RPM:\t\t{summary["stats"]["rpmr"][2]:.2f}")
    print(f"Minimum CMD:\t\t{summary["stats"]["cmdr"][0]}")
    print(f"Maximum CMD:\t\t{summary["stats"]["cmdr"][1]}\n")

    print("DRIVER INPUT\n------------")
    print(f"Average throttle:\t{summary["stats"]["average_throttle"]:.2f}%")
    print(f"steering activity:\t{summary["stats"]["steering_activity"]:.2f}%\n")

def format_events(summary):
    print("EVENTS\n------")
    print(f"Warnings:\t\t{summary["events"]["warnings"]}")
    print(f"Errors:\t\t\t{summary["events"]["errors"]}")
    print(f"High temp:\t\t{summary["events"]["high_temperature"]}")
    print(f"Low supply:\t\t{summary["events"]["low_supply"]}")
    print(f"Motor mismatch:\t\t{summary["events"]["motor_mismatch"]}")
    print(f"Motor stall:\t\t{summary["events"]["motor_stall"]}\n")

def format_malformed(summary):
    print("MALFORMED LINES\n---------------")
    for i in range(len(summary["malformed"])):
        print(f"Line {summary["malformed"][i][0]}:\t{summary["malformed"][i][1]}")

def format_report(summary):

    print("\n\nVEHICLE TELEMETRY REPORT\n========================\n")
    print(f"Input file: {summary["file"]}\n")

    print("SESSION\n-------")
    print(f"Duration:\t\t{summary["duration"]}")
    print(f"Samples:\t\t{summary["samples"]} line(s)")
    print(f"Valid telemetry:\t{summary["valid_lines"]} line(s)")
    print(f"Malformed telemetry:\t{summary["malformed_lines"]} line(s)\n")

    format_stats(summary)
    format_events(summary)
    format_malformed(summary)

    print()


def export_csv(records, filename):
    fieldnames = ['timestamp','level','temp_c','supply_v','rpm_l','rpm_r','cmd_l','cmd_r','throttle','steer']
    with open(filename, "w") as file:
        writer = csv.DictWriter(file , fieldnames = fieldnames, restval='-')
        writer.writeheader()
        for i in range(len(records)):
            try:
                writer.writerow({'timestamp': records[i]["timestamp"], 'level': records[i]["level"], 'temp_c': records[i]["temp_c"], 'supply_v': records[i]["supply_v"], 'rpm_l': records[i]["rpm_l"], 'rpm_r': records[i]["rpm_r"], 'cmd_l': records[i]["cmd_l"], 'cmd_r': records[i]["cmd_r"], 'throttle': records[i]["throttle"], 'steer': records[i]["steer"]})
            except KeyError:
                continue

def export_json(summary, filename):
    with open(filename, "w") as file:
        json.dump(summary, file, indent=4)

if __name__ == "__main__":
    main()
