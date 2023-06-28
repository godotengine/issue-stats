#!/usr/bin/env python3
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv
import os


def main() -> None:
    load_dotenv()

    transport = AIOHTTPTransport(
        url="https://api.github.com/graphql",
        headers={
            "Authorization": f"Bearer {os.getenv('GODOT_ISSUES_STATS_GITHUB_TOKEN')}"
        },
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    # TODO: Query more than 100 issues by performing several requests.
    query = gql(
        """
        query {
        repository(owner: "godotengine", name: "godot") {
            issues(last: 100) {
                edges {
                    node {
                        body
                        author {
                            login
                        }
                    }
                }
            }
        }
    }
    """
    )

    result = client.execute(query)
    # Array of dictionaries with user and system information string.
    user_system_infos = []

    # Counters for all statistics (values are a set of usernames).
    # A set is used, so that each user may only increment a given counter once.
    # A single user may increment multiple counters in the same category,
    # as they may report issues with different hardware or operating systems.
    statistics = {
        "os": {
            "windows": {
                "11": set(),
                "10": set(),
                "8.1": set(),
                "8": set(),
                "7": set(),
                "unknown": set(),
            },
            "linux": {
                "ubuntu": set(),
                "fedora": set(),
                "arch": set(),
                "mint": set(),
                "unknown": set(),
            },
            "macos": {
                "14": set(),
                "13": set(),
                "12": set(),
                "11": set(),
                "10.15": set(),
                "10.14": set(),
                "10.13": set(),
                "10.12": set(),
                "unknown": set(),
            },
            "android": {
                "14": set(),
                "13": set(),
                "12": set(),
                "11": set(),
                "10": set(),
                "9": set(),
                "8": set(),
                "7": set(),
                "6": set(),
                "5": set(),
                "unknown": set(),
            },
            "ios": {
                "17": set(),
                "16": set(),
                "15": set(),
                "14": set(),
                "13": set(),
                "12": set(),
                "11": set(),
                "10": set(),
                "unknown": set(),
            },
            "web": {
                "firefox": set(),
                "chrome": set(),
                "opera": set(),
                "edge": set(),
                "safari": set(),
                "unknown": set(),
            },
        },
        "cpu": {
            "amd": {
                "zen4": set(),
                "zen3": set(),
                "zen2": set(),
                "zen+": set(),
                "zen": set(),
                "piledriver": set(),
                "bulldozer": set(),
                "phenom": set(),
                "unknown": set(),
            },
            "intel": {
                "meteor_lake": set(),
                "raptor_lake": set(),
                "alder_lake": set(),
                "rocket_lake": set(),
                "ice_lake": set(),
                "coffee_lake_refresh": set(),
                "coffee_lake": set(),
                "kaby_lake": set(),
                "skylake": set(),
                "haswell": set(),
                "ivy_bridge": set(),
                "sandy_bridge": set(),
                "nehalem": set(),
                "core2": set(),
                "unknown": set(),
            },
        },
        "gpu": {
            "amd": {
                "rdna3": set(),
                "rdna2": set(),
                "rdna": set(),
                "vega": set(),
                "polaris": set(),
                "gcn3.0": set(),
                "gcn2.0": set(),
                "gcn1.0": set(),
                "vliw4": set(),
                "igp_rdna3": set(),
                "igp_rdna2": set(),
                "igp_vega": set(),
                "unknown": set(),
            },
            "intel": {
                "arc_alchemist": set(),
                "igp_meteor_lake": set(),
                "igp_raptor_lake": set(),
                "igp_alder_lake": set(),
                "igp_rocket_lake": set(),
                "igp_ice_lake": set(),
                "igp_coffee_lake_refresh": set(),
                "igp_coffee_lake": set(),
                "igp_kaby_lake": set(),
                "igp_skylake": set(),
                "igp_haswell": set(),
                "igp_ivy_bridge": set(),
                "igp_sandy_bridge": set(),
                "unknown": set(),
            },
            "nvidia": {
                "ada_lovelace": set(),
                "ampere": set(),
                "turing": set(),
                "pascal": set(),
                "maxwell": set(),
                "kepler": set(),
                "fermi": set(),
                "tesla": set(),
                "unknown": set(),
            },
        },
    }

    for node in result["repository"]["issues"]["edges"]:
        user = node["node"]["author"]["login"]
        body = node["node"]["body"]
        system_info_index = body.find("### System information\n\n")
        issue_description_index = body.find("\n\n### Issue description")
        if system_info_index != -1 and issue_description_index != -1:
            system_info_index_end = system_info_index + len(
                "### System information\n\n"
            )
            system_information = body[system_info_index_end:issue_description_index]
            user_system_infos.append(
                {"user": user, "system_information": system_information}
            )

            # Gather statistics for each issue reported.
            if system_information.lower().find("windows 11") != -1:
                statistics["os"]["windows"]["11"].add(user)
            elif system_information.lower().find("windows 10") != -1:
                statistics["os"]["windows"]["10"].add(user)
            elif system_information.lower().find("windows 8.1") != -1:
                statistics["os"]["windows"]["8.1"].add(user)
            elif system_information.lower().find("windows 8") != -1:
                statistics["os"]["windows"]["8"].add(user)
            elif system_information.lower().find("windows 7") != -1:
                statistics["os"]["windows"]["7"].add(user)
            elif system_information.lower().find("windows") != -1:
                statistics["os"]["windows"]["unknown"].add(user)

            if system_information.lower().find("ubuntu") != -1:
                statistics["os"]["linux"]["ubuntu"].add(user)
            elif system_information.lower().find("linux") != -1:
                statistics["os"]["linux"]["unknown"].add(user)

            # TODO: Gather more statistics.

    for info in user_system_infos:
        print(info["user"])
        print(info["system_information"])
        print()

    print(statistics)


if __name__ == "__main__":
    main()
