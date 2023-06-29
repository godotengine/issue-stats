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
                "debian": set(),
                "mint": set(),
                "arch": set(),
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
        "cpu_core_count": {
            # Number of physical CPU cores.
            # On CPUs with hybrid topologies (such as 12th generation Intel and newer),
            # this is the sum of P-cores and E-cores.
            "1": set(),
            "2": set(),
            "3": set(),
            "4": set(),
            "6": set(),
            "8": set(),
            "10": set(),
            "12": set(),
            "16": set(),
            "24": set(),
            "32": set(),
            "48": set(),
            "64": set(),
            "96": set(),
        },
        "cpu_x86_features": {
            # Support for modern x86 CPU features, which binaries can be optimized for.
            # Currently, Godot only requires SSE2 (which is the baseline for all x86_64 CPUs).
            # The highest supported CPU feature set is stored for each user
            # (e.g. support for AVX512 implies support for AVX2, AVX and SSE 4.2).
            "avx512": set(),
            "avx2": set(),
            "avx": set(),
            "sse4.2": set(),
        },
        "cpu_passmark_score": {
            # Scores from <https://www.cpubenchmark.net/>.
            "single_thread": {
                "<1000": set(),
                "1000-1500": set(),
                "1500-2000": set(),
                "2000-2500": set(),
                "2500-3000": set(),
                "3000-3500": set(),
                "3500-4000": set(),
                "4000-4500": set(),
                ">4500": set(),
            },
            "multi_thread": {
                "<5000": set(),
                "5000-10000": set(),
                "10000-20000": set(),
                "20000-30000": set(),
                "30000-40000": set(),
                "40000-50000": set(),
                "50000-60000": set(),
                ">60000": set(),
            },
        },
        "gpu": {
            "amd": {
                "dedicated_rdna3": set(),
                "dedicated_rdna2": set(),
                "dedicated_rdna1": set(),
                "dedicated_gcn5.0": set(),
                "dedicated_gcn4.0": set(),
                "dedicated_gcn3.0": set(),
                "dedicated_gcn2.0": set(),
                "dedicated_gcn1.0": set(),
                "dedicated_vliw4": set(),
                "integrated_rdna3": set(),
                "integrated_rdna2": set(),
                "integrated_gcn5.0": set(),
                "unknown": set(),
            },
            "intel": {
                "dedicated_arc_alchemist": set(),
                "integrated_gen12": set(),  # Rocket Lake/Alder Lake/Raptor Lake
                # There's no way to detect gen11 (Ice Lake) IGPs based on GPU model name alone.
                # There are gen10 IGPs.
                "integrated_gen9.5": set(),  # Kaby Lake/Coffee Lake/Coffee Lake Refresh
                "integrated_gen9": set(),  # Skylake
                "integrated_gen8": set(),  # Broadwell
                "integrated_gen7.5": set(),  # Haswell
                "integrated_gen7": set(),  # Ivy Bridge
                "integrated_gen6": set(),  # Sandy Bridge
                "unknown": set(),
            },
            "nvidia": {
                "dedicated_ada_lovelace": set(),
                "dedicated_ampere": set(),
                "dedicated_turing": set(),
                "dedicated_pascal": set(),
                "dedicated_maxwell": set(),
                "dedicated_kepler": set(),
                "dedicated_fermi": set(),
                "unknown": set(),
            },
        },
        "gpu_vram": {
            # Only dedicated GPUs increment this statistic.
            "less_than_2_gb": set(),
            "2_gb": set(),
            "3_gb": set(),
            "4_gb": set(),
            "6_gb": set(),
            "8_gb": set(),
            "10_gb": set(),
            "11_gb": set(),
            "12_gb": set(),
            "16_gb": set(),
            "20_gb": set(),
            "24_gb": set(),
            "more_than_24_gb": set(),
        },
        "gpu_passmark_score": {
            # Scores from <https://www.videocardbenchmark.net/>.
            "<2500": set(),
            "2500-5000": set(),
            "5000-10000": set(),
            "10000-15000": set(),
            "15000-20000": set(),
            "20000-25000": set(),
            "25000-30000": set(),
            ">30000": set(),
        },
        "gpu_raytracing": {
            # GPUs with hardware-accelerated raytracing (not used in Godot yet).
            "dedicated": {
                "yes": set(),
                "no": set(),
            },
            "integrated": {
                "yes": set(),
                "no": set(),
            },
        },
        "gpu_vrs": {
            # GPUs with support for variable-rate shading (which Godot 4 supports).
            "dedicated": {
                "yes": set(),
                "no": set(),
            },
            "integrated": {
                "yes": set(),
                "no": set(),
            },
        },
        "gpu_mesh_shaders": {
            # GPUs with support for mesh shaders (not used in Godot yet).
            "dedicated": {
                "yes": set(),
                "no": set(),
            },
            "integrated": {
                "yes": set(),
                "no": set(),
            },
        },
    }

    for node in result["repository"]["issues"]["edges"]:
        user = node["node"]["author"]["login"]
        body = node["node"]["body"]
        # Only issues reported with the issue template form can be scanned with this approach.
        # This means issues reported before 2020 can't be scanned.
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

            # Make the search case-insensitive and punctuation-insensitive.
            system_information_trimmed = (
                system_information.lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(":", "")
                .replace(",", "")
                .replace("(r)", "")
                .replace("(tm)", "")
                .replace("graphics", "")  # Makes it easier to parse "Intel HD Graphics ...".
            )
            print(system_information_trimmed)

            # Gather statistics for each issue reported.
            if "windows11" in system_information_trimmed:
                statistics["os"]["windows"]["11"].add(user)
            elif "windows10" in system_information_trimmed:
                statistics["os"]["windows"]["10"].add(user)
            elif "windows8.1" in system_information_trimmed:
                statistics["os"]["windows"]["8.1"].add(user)
            elif "windows8" in system_information_trimmed:
                statistics["os"]["windows"]["8"].add(user)
            elif "windows7" in system_information_trimmed:
                statistics["os"]["windows"]["7"].add(user)
            elif "windows" in system_information_trimmed:
                statistics["os"]["windows"]["unknown"].add(user)

            if "ubuntu" in system_information_trimmed:
                statistics["os"]["linux"]["ubuntu"].add(user)
            elif "fedora" in system_information_trimmed:
                statistics["os"]["linux"]["fedora"].add(user)
            elif "debian" in system_information_trimmed:
                statistics["os"]["linux"]["debian"].add(user)
            elif "mint" in system_information_trimmed:
                statistics["os"]["linux"]["mint"].add(user)
            elif "arch" in system_information_trimmed:
                statistics["os"]["linux"]["arch"].add(user)
            elif "linux" in system_information_trimmed:
                statistics["os"]["linux"]["unknown"].add(user)

            if (
                "macos13" in system_information_trimmed
                or "macosventura" in system_information_trimmed
            ):
                statistics["os"]["macos"]["13"].add(user)
            elif (
                "macos12" in system_information_trimmed
                or "macosmonterey" in system_information_trimmed
            ):
                statistics["os"]["macos"]["12"].add(user)
            elif (
                "macos11" in system_information_trimmed
                or "macosbigsur" in system_information_trimmed
            ):
                statistics["os"]["macos"]["11"].add(user)
            elif (
                "macos10.15" in system_information_trimmed
                or "macoscatalina" in system_information_trimmed
            ):
                statistics["os"]["macos"]["10.15"].add(user)
            elif (
                "macos10.14" in system_information_trimmed
                or "macosmojave" in system_information_trimmed
            ):
                statistics["os"]["macos"]["10.14"].add(user)
            elif (
                "macos10.13" in system_information_trimmed
                or "macoshighsierra" in system_information_trimmed
            ):
                statistics["os"]["macos"]["10.13"].add(user)
            elif (
                "macos10.12" in system_information_trimmed
                or "macossierra" in system_information_trimmed
            ):
                statistics["os"]["macos"]["10.12"].add(user)
            elif "macos" in system_information_trimmed:
                statistics["os"]["macos"]["unknown"].add(user)

            if "android13" in system_information_trimmed:
                statistics["os"]["android"]["13"].add(user)
            elif "android12" in system_information_trimmed:
                statistics["os"]["android"]["12"].add(user)
            elif "android11" in system_information_trimmed:
                statistics["os"]["android"]["11"].add(user)
            elif "android10" in system_information_trimmed:
                statistics["os"]["android"]["10"].add(user)
            elif "android9" in system_information_trimmed:
                statistics["os"]["android"]["9"].add(user)
            elif "android8" in system_information_trimmed:
                statistics["os"]["android"]["8"].add(user)
            elif "android7" in system_information_trimmed:
                statistics["os"]["android"]["7"].add(user)
            elif "android6" in system_information_trimmed:
                statistics["os"]["android"]["6"].add(user)
            elif "android5" in system_information_trimmed:
                statistics["os"]["android"]["5"].add(user)
            elif "android" in system_information_trimmed:
                statistics["os"]["android"]["unknown"].add(user)

            if "ios17" in system_information_trimmed:
                statistics["os"]["ios"]["17"].add(user)
            elif "ios16" in system_information_trimmed:
                statistics["os"]["ios"]["16"].add(user)
            elif "ios15" in system_information_trimmed:
                statistics["os"]["ios"]["15"].add(user)
            elif "ios14" in system_information_trimmed:
                statistics["os"]["ios"]["14"].add(user)
            elif "ios13" in system_information_trimmed:
                statistics["os"]["ios"]["13"].add(user)
            elif "ios12" in system_information_trimmed:
                statistics["os"]["ios"]["12"].add(user)
            elif "ios11" in system_information_trimmed:
                statistics["os"]["ios"]["11"].add(user)
            elif "ios10" in system_information_trimmed:
                statistics["os"]["ios"]["10"].add(user)
            elif "ios" in system_information_trimmed:
                statistics["os"]["ios"]["unknown"].add(user)

            if "firefox" in system_information_trimmed:
                statistics["os"]["web"]["firefox"].add(user)
            elif "chrome" in system_information_trimmed:
                statistics["os"]["web"]["chrome"].add(user)
            elif "opera" in system_information_trimmed:
                statistics["os"]["web"]["opera"].add(user)
            elif "edge" in system_information_trimmed:
                statistics["os"]["web"]["edge"].add(user)
            elif "safari" in system_information_trimmed:
                statistics["os"]["web"]["safari"].add(user)
            elif "web" in system_information_trimmed:
                statistics["os"]["web"]["unknown"].add(user)

            # TODO: Add more Intel CPUs. Tweak detection to also allow "intel<number>" and "core<number>".
            # TODO: Add Passmark scores for CPUs and GPUs.
            if "i76700" in system_information_trimmed:
                statistics["cpu"]["intel"]["skylake"].add(user)
                statistics["cpu_core_count"]["4"].add(user)
                statistics["cpu_x86_features"]["avx2"].add(user)
            elif (
                "intelcore" in system_information_trimmed
                or "inteli" in system_information_trimmed
            ):
                # Second part of the `if` statement is for users who write "Intel i7" instead of "Intel Core i7".
                statistics["cpu"]["intel"]["unknown"].add(user)

            # TODO: Add more AMD CPUs.
            # NOTE: Unlike Intel CPUs, detection does not allow "amd<number>" as this syntax is used for GPUs instead.
            #       There would be some ambiguities otherwise, such as Ryzen 5 7600 versus Radeon RX 7600.
            if (
                "ryzen55600x" in system_information_trimmed
                or "ryzen5600x" in system_information_trimmed
            ):
                statistics["cpu"]["amd"]["zen3"].add(user)
                statistics["cpu_core_count"]["6"].add(user)
                statistics["cpu_x86_features"]["avx2"].add(user)
            elif (
                "ryzen" in system_information_trimmed
                or "fx" in system_information_trimmed
            ):
                statistics["cpu"]["amd"]["unknown"].add(user)

            # NOTE: In this scanning, laptop GPUs are only separated from desktop GPUs since Ampere.
            #       This may not be reliable in all cases if the user has removed the "Mobile"
            #       or "Laptop" suffix from the model name.
            if (
                "rtx4090" in system_information_trimmed
                or "geforce4090" in system_information_trimmed
                or "nvidia4090" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["24_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "4090laptop" in system_information_trimmed
                or "4090mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx4080" in system_information_trimmed
                or "geforce4080" in system_information_trimmed
                or "nvidia4080" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "4080laptop" in system_information_trimmed
                or "4080mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx4070ti" in system_information_trimmed
                or "geforce4070ti" in system_information_trimmed
                or "nvidia4070ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx4070" in system_information_trimmed
                or "geforce4070" in system_information_trimmed
                or "nvidia4070" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "4070laptop" in system_information_trimmed
                or "4070mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx4060ti" in system_information_trimmed
                or "geforce4060ti" in system_information_trimmed
                or "nvidia4060ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                # Assume 8 GB variant, which is much more widespread than the 16 GB one.
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx4060" in system_information_trimmed
                or "geforce4060" in system_information_trimmed
                or "nvidia4060" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "4060laptop" in system_information_trimmed
                or "4060mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "4050laptop" in system_information_trimmed
                or "4050mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx3090" in system_information_trimmed
                or "geforce3090" in system_information_trimmed
                or "nvidia3090" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["10_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx3080ti" in system_information_trimmed
                or "geforce3080ti" in system_information_trimmed
                or "nvidia3080ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["10_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3080tilaptop" in system_information_trimmed
                or "3080timobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx3080" in system_information_trimmed
                or "geforce3080" in system_information_trimmed
                or "nvidia3080" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                # Assume 8 GB variant, which is much more widespread than the 16 GB one.
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3080laptop" in system_information_trimmed
                or "3080mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx3070ti" in system_information_trimmed
                or "geforce3070ti" in system_information_trimmed
                or "nvidia3070ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3070tilaptop" in system_information_trimmed
                or "3070timobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx3070" in system_information_trimmed
                or "geforce3070" in system_information_trimmed
                or "nvidia3070" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3070laptop" in system_information_trimmed
                or "3070mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3060tilaptop" in system_information_trimmed
                or "3060timobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx3060" in system_information_trimmed
                or "geforce3060" in system_information_trimmed
                or "nvidia3060" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                # Assume 12 GB variant, which is much more widespread than the 8 GB one.
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3060laptop" in system_information_trimmed
                or "3060mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3050tilaptop" in system_information_trimmed
                or "3050timobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx3050" in system_information_trimmed
                or "geforce3050" in system_information_trimmed
                or "nvidia3050" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "3050laptop" in system_information_trimmed
                or "3050mobile" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                # Assume 4 GB variant, which is much more widespread than the 6 GB one.
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx2080ti" in system_information_trimmed
                or "geforce2080ti" in system_information_trimmed
                or "nvidia2080ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["11_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx2080super" in system_information_trimmed
                or "geforce2080super" in system_information_trimmed
                or "nvidia2080super" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["11_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx2080" in system_information_trimmed
                or "geforce2080" in system_information_trimmed
                or "nvidia2080" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx2070super" in system_information_trimmed
                or "geforce2070super" in system_information_trimmed
                or "nvidia2070super" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx2070" in system_information_trimmed
                or "geforce2070" in system_information_trimmed
                or "nvidia2070" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx2060super" in system_information_trimmed
                or "geforce2060super" in system_information_trimmed
                or "nvidia2060super" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rtx2060" in system_information_trimmed
                or "geforce2060" in system_information_trimmed
                or "nvidia2060" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "gtx1660ti" in system_information_trimmed
                or "geforce1660ti" in system_information_trimmed
                or "nvidia1660ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "gtx1660super" in system_information_trimmed
                or "geforce1660super" in system_information_trimmed
                or "nvidia1660super" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "gtx1660" in system_information_trimmed
                or "geforce1660" in system_information_trimmed
                or "nvidia1660" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "gtx1650super" in system_information_trimmed
                or "geforce1650super" in system_information_trimmed
                or "nvidia1650super" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "gtx1650" in system_information_trimmed
                or "geforce1650" in system_information_trimmed
                or "nvidia1650" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "gtx1630" in system_information_trimmed
                or "geforce1630" in system_information_trimmed
                or "nvidia1630" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "gtx1080ti" in system_information_trimmed
                or "geforce1080ti" in system_information_trimmed
                or "nvidia1080ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_pascal"].add(user)
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx1080" in system_information_trimmed
                or "geforce1080" in system_information_trimmed
                or "nvidia1080" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_pascal"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx1070ti" in system_information_trimmed
                or "geforce1070ti" in system_information_trimmed
                or "nvidia1070ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_pascal"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx1070" in system_information_trimmed
                or "geforce1070" in system_information_trimmed
                or "nvidia1070" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_pascal"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx1060" in system_information_trimmed
                or "geforce1060" in system_information_trimmed
                or "nvidia1060" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_pascal"].add(user)
                # Assume 6 GB variant, which is much more widespread than the 3 GB one.
                # This also applies to the Passmark score, as its 6 GB variant is faster
                # than the 3 GB thanks to additional CUDA cores.
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx1050ti" in system_information_trimmed
                or "geforce1050ti" in system_information_trimmed
                or "nvidia1050ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_pascal"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx1050" in system_information_trimmed
                or "geforce1050" in system_information_trimmed
                or "nvidia1050" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_pascal"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx980ti" in system_information_trimmed
                or "geforce980ti" in system_information_trimmed
                or "nvidia980ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_maxwell"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx980" in system_information_trimmed
                or "geforce980" in system_information_trimmed
                or "nvidia980" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_maxwell"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx970" in system_information_trimmed
                or "geforce970" in system_information_trimmed
                or "nvidia970" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_maxwell"].add(user)
                # Count as a GPU with 3 GB of VRAM, since only 3.5 GB of VRAM
                # (out of 4 GB physically present) are full-speed on a GeForce GTX 970.
                statistics["gpu_vram"]["3_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx960" in system_information_trimmed
                or "geforce960" in system_information_trimmed
                or "nvidia960" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_maxwell"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx950" in system_information_trimmed
                or "geforce950" in system_information_trimmed
                or "nvidia950" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_maxwell"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx750ti" in system_information_trimmed
                or "geforce750ti" in system_information_trimmed
                or "nvidia750ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_maxwell"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx750" in system_information_trimmed
                or "geforce750" in system_information_trimmed
                or "nvidia750" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_maxwell"].add(user)
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx690" in system_information_trimmed
                or "geforce690" in system_information_trimmed
                or "nvidia690" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                # Dual-GPU card; since Godot doesn't support multi-GPU, only account for the VRAM of a single GPU.
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx680" in system_information_trimmed
                or "geforce680" in system_information_trimmed
                or "nvidia680" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx670" in system_information_trimmed
                or "geforce670" in system_information_trimmed
                or "nvidia670" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx660ti" in system_information_trimmed
                or "geforce660ti" in system_information_trimmed
                or "nvidia660ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx660" in system_information_trimmed
                or "geforce660" in system_information_trimmed
                or "nvidia660" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx650ti" in system_information_trimmed
                or "geforce650ti" in system_information_trimmed
                or "nvidia650ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx650" in system_information_trimmed
                or "geforce650" in system_information_trimmed
                or "nvidia650" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx590" in system_information_trimmed
                or "geforce590" in system_information_trimmed
                or "nvidia590" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                # Dual-GPU card; since Godot doesn't support multi-GPU, only account for the VRAM of a single GPU.
                # 1.5 GB of VRAM per GPU; round down to 1 GB.
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx580" in system_information_trimmed
                or "geforce580" in system_information_trimmed
                or "nvidia580" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                # 1.5 GB of VRAM; round down to 1 GB.
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx570" in system_information_trimmed
                or "geforce570" in system_information_trimmed
                or "nvidia570" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                # 1.25 GB of VRAM; round down to 1 GB.
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx560ti" in system_information_trimmed
                or "geforce560ti" in system_information_trimmed
                or "nvidia560ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx560" in system_information_trimmed
                or "geforce560" in system_information_trimmed
                or "nvidia560" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "gtx550ti" in system_information_trimmed
                or "geforce550ti" in system_information_trimmed
                or "nvidia550ti" in system_information_trimmed
            ):
                statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                statistics["gpu_vram"]["1_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif "gt710" in system_information_trimmed:
                # The GeForce GT 710 is a Fermi GPU despite being in the 700 series.
                statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif "nvidia" in system_information_trimmed:
                statistics["gpu"]["nvidia"]["unknown"].add(user)

            if (
                "rx7900xtx" in system_information_trimmed
                or "radeon7900xtx" in system_information_trimmed
                or "amd7900xtx" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna3"].add(user)
                statistics["gpu_vram"]["24_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx7900xt" in system_information_trimmed
                or "radeon7900xt" in system_information_trimmed
                or "amd7900xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna3"].add(user)
                statistics["gpu_vram"]["20_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx7600xt" in system_information_trimmed
                or "radeon7600xt" in system_information_trimmed
                or "amd7600xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna3"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6950xt" in system_information_trimmed
                or "radeon6950xt" in system_information_trimmed
                or "amd6950xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6900xt" in system_information_trimmed
                or "radeon6900xt" in system_information_trimmed
                or "amd6900xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6850xt" in system_information_trimmed
                or "radeon6850xt" in system_information_trimmed
                or "amd6850xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6800xt" in system_information_trimmed
                or "radeon6800xt" in system_information_trimmed
                or "amd6800xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6800" in system_information_trimmed
                or "radeon6800" in system_information_trimmed
                or "amd6800" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6750xt" in system_information_trimmed
                or "radeon6750xt" in system_information_trimmed
                or "amd6750xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6700xt" in system_information_trimmed
                or "radeon6700xt" in system_information_trimmed
                or "amd6700xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["12_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6700" in system_information_trimmed
                or "radeon6700" in system_information_trimmed
                or "amd6700" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["10_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6650xt" in system_information_trimmed
                or "radeon6650xt" in system_information_trimmed
                or "amd6650xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6600xt" in system_information_trimmed
                or "radeon6600xt" in system_information_trimmed
                or "amd6600xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6600" in system_information_trimmed
                or "radeon6600" in system_information_trimmed
                or "amd6600" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6500xt" in system_information_trimmed
                or "radeon6500xt" in system_information_trimmed
                or "amd6500xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx6400" in system_information_trimmed
                or "radeon6400" in system_information_trimmed
                or "amd6400" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna2"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif (
                "rx5700xt" in system_information_trimmed
                or "radeon5700xt" in system_information_trimmed
                or "amd5700xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna1"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx5700" in system_information_trimmed
                or "radeon5700" in system_information_trimmed
                or "amd5700" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna1"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx5600xt" in system_information_trimmed
                or "radeon5600xt" in system_information_trimmed
                or "amd5600xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna1"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx5500xt" in system_information_trimmed
                or "radeon5500xt" in system_information_trimmed
                or "amd5500xt" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_rdna1"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif "radeonvii" in system_information_trimmed:
                statistics["gpu"]["amd"]["dedicated_gcn5.0"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif "vega64" in system_information_trimmed:
                statistics["gpu"]["amd"]["dedicated_gcn5.0"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif "vega56" in system_information_trimmed:
                statistics["gpu"]["amd"]["dedicated_gcn5.0"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx590" in system_information_trimmed
                or "radeon590" in system_information_trimmed
                or "amd590" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx580" in system_information_trimmed
                or "radeon580" in system_information_trimmed
                or "amd580" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx570" in system_information_trimmed
                or "radeon570" in system_information_trimmed
                or "amd570" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx560" in system_information_trimmed
                or "radeon560" in system_information_trimmed
                or "amd560" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx550" in system_information_trimmed
                or "radeon550" in system_information_trimmed
                or "amd550" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx480" in system_information_trimmed
                or "radeon480" in system_information_trimmed
                or "amd480" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx470" in system_information_trimmed
                or "radeon470" in system_information_trimmed
                or "amd470" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif (
                "rx460" in system_information_trimmed
                or "radeon460" in system_information_trimmed
                or "amd460" in system_information_trimmed
            ):
                statistics["gpu"]["amd"]["dedicated_gcn4.0"].add(user)
                statistics["gpu_vram"]["2_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
            elif "radeon" in system_information_trimmed:
                statistics["gpu"]["amd"]["unknown"].add(user)

            if "a780" in system_information_trimmed:
                statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif "a770" in system_information_trimmed:
                statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                statistics["gpu_vram"]["16_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif "a750" in system_information_trimmed:
                statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif "a580" in system_information_trimmed:
                statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                statistics["gpu_vram"]["8_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif "a380" in system_information_trimmed:
                statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                statistics["gpu_vram"]["6_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif "a350" in system_information_trimmed:
                statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif "a310" in system_information_trimmed:
                statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                statistics["gpu_vram"]["4_gb"].add(user)
                statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
            elif "uhd770" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd750" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd730" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd710" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "irisplus655" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "irisplus645" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd630" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd620" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd617" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd615" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "uhd610" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "irisplus650" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "irisplus640" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd630" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd620" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd615" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd610" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "irispro580" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "iris550" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "iris540" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd530" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd520" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd515" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd510" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "irispro6200" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "iris6100" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd6000" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd5600" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd5500" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd5300" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "irispro5200" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "iris5100" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd5000" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd4600" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd4400" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd4200" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd4000" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd2500" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen7"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd3000" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen6"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif "hd2000" in system_information_trimmed:
                statistics["gpu"]["intel"]["integrated_gen6"].add(user)
                statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                statistics["gpu_vrs"]["integrated"]["no"].add(user)
                statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
            elif (
                "irisxe" in system_information_trimmed
                or "intelhd" in system_information_trimmed
            ):
                statistics["gpu"]["intel"]["unknown"].add(user)

    for info in user_system_infos:
        print(info["user"], " \t", info["system_information"])

    print(f"Number of scannable reports: {len(user_system_infos)}")
    print()
    print(statistics)


if __name__ == "__main__":
    main()
