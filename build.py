#!/usr/bin/env python3
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from typing_extensions import Final


def main() -> None:
    load_dotenv()

    transport: Final = AIOHTTPTransport(
        url="https://api.github.com/graphql",
        headers={
            "Authorization": f"Bearer {os.getenv('GODOT_ISSUES_STATS_GITHUB_TOKEN')}"
        },
    )
    client: Final = Client(transport=transport, fetch_schema_from_transport=True)

    results: Final = []
    cursor = None
    # Get the 30×100 = 3,000 last issues.
    # TODO: Retry requests a few times if they fail.
    num_queries = 30
    for i in range(num_queries):
        print(f"Running query {i + 1}/{num_queries}...")
        query = gql(
            """
            query($cursor: String) {
                repository(owner: "godotengine", name: "godot") {
                    issues(last: 100, orderBy: { direction: ASC, field: CREATED_AT }, before: $cursor) {
                        edges {
                            cursor
                            node {
                                body
                                createdAt
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

        # We're querying the first page, so we don't need to supply a valid cursor.
        # GQL will take care of not submitting the variable if it's set to `None`.
        result = client.execute(query, variable_values={"cursor": cursor})
        results.append(result)
        # Get the cursor value of the last returned item, as we need it for subsequent requests (pagination).
        cursor = result["repository"]["issues"]["edges"][0]["cursor"]
        if i == 0:
            # Store the date and time of the most recent report.
            # Reports are sorted by ascending date, so this is the last item in the first query.
            last_report_date = result["repository"]["issues"]["edges"][-1]["node"][
                "createdAt"
            ]
        if i == num_queries - 1:
            # Store the date and time of the oldest report.
            # Reports are sorted by ascending date, so this is the first item in the last query.
            first_report_date = result["repository"]["issues"]["edges"][0]["node"][
                "createdAt"
            ]

    # Array of dictionaries with user and system information string.
    user_system_infos: Final = []

    # Counters for all statistics (values are a set of usernames).
    # A set is used, so that each user may only increment a given counter once.
    # A single user may increment multiple counters in the same category,
    # as they may report issues with different hardware or operating systems.
    statistics: Dict[str, Any] = {
        "os": {
            "windows": {
                "windows_11": set(),
                "windows_10": set(),
                "windows_8.1": set(),
                "windows_8": set(),
                "windows_7": set(),
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
                "macos_14": set(),
                "macos_13": set(),
                "macos_12": set(),
                "macos_11": set(),
                "macos_10.15": set(),
                "macos_10.14": set(),
                "macos_10.13": set(),
                "macos_10.12": set(),
                "unknown": set(),
            },
            "android": {
                "android_14": set(),
                "android_13": set(),
                "android_12": set(),
                "android_11": set(),
                "android_10": set(),
                "android_9": set(),
                "android_8": set(),
                "android_7": set(),
                "android_6": set(),
                "android_5": set(),
                "unknown": set(),
            },
            "ios": {
                "ios_17": set(),
                "ios_16": set(),
                "ios_15": set(),
                "ios_14": set(),
                "ios_13": set(),
                "ios_12": set(),
                "ios_11": set(),
                "ios_10": set(),
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
                "zen1": set(),
                "piledriver": set(),
                "bulldozer": set(),
                "unknown": set(),
            },
            "intel": {
                "raptor_lake": set(),
                "alder_lake": set(),
                "rocket_lake": set(),
                "comet_lake": set(),
                "coffee_lake_refresh": set(),
                "coffee_lake": set(),
                "kaby_lake": set(),
                "skylake": set(),
                "haswell": set(),
                "ivy_bridge": set(),
                "sandy_bridge": set(),
                "unknown": set(),
            },
        },
        "cpu_core_count": {
            # Number of physical CPU cores.
            # On CPUs with hybrid topologies (such as 12th generation Intel and newer),
            # this is the sum of P-cores and E-cores.
            ">32_cores": set(),
            "32_cores": set(),
            "24_cores": set(),
            "16_cores": set(),
            "14_cores": set(),
            "12_cores": set(),
            "10_cores": set(),
            "8_cores": set(),
            "6_cores": set(),
            "4_cores": set(),
            "2_cores": set(),
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
            "multi_thread": {
                ">60000": set(),
                "50000-60000": set(),
                "40000-50000": set(),
                "30000-40000": set(),
                "20000-30000": set(),
                "10000-20000": set(),
                "5000-10000": set(),
                "<5000": set(),
            },
            "single_thread": {
                ">4500": set(),
                "4000-4500": set(),
                "3500-4000": set(),
                "3000-3500": set(),
                "2500-3000": set(),
                "2000-2500": set(),
                "1500-2000": set(),
                "<1500": set(),
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
                # There are no gen10 IGPs.
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
            ">24_gb": set(),
            "24_gb": set(),
            "20_gb": set(),
            "16_gb": set(),
            "12_gb": set(),
            "11_gb": set(),
            "10_gb": set(),
            "8_gb": set(),
            "6_gb": set(),
            "4_gb": set(),
            "3_gb": set(),
            "2_gb": set(),
            "1_gb": set(),
        },
        "gpu_passmark_score": {
            # Scores from <https://www.videocardbenchmark.net/>.
            ">30000": set(),
            "25000-30000": set(),
            "20000-25000": set(),
            "15000-20000": set(),
            "10000-15000": set(),
            "5000-10000": set(),
            "2500-5000": set(),
            "<2500": set(),
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

    for result in results:
        for node in result["repository"]["issues"]["edges"]:
            # Handle deleted ("ghost") users.
            user = (
                node["node"]["author"]["login"]
                if node["node"]["author"] is not None
                else "ghost"
            )
            # Fix CRLF line endings causing issues with detection,
            # as some issue reports use them instead of LF line endings.
            body = node["node"]["body"].replace("\r\n", "\n")
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
                    .replace(
                        "graphics", ""
                    )  # Makes it easier to parse "Intel HD Graphics ...".
                    .replace(
                        "pro", ""
                    )  # Makes it easier to parse "Ryzen PRO" (these are very close to their non-PRO counterparts).
                )

                # Gather statistics for each issue reported.
                if "windows11" in system_information_trimmed:
                    statistics["os"]["windows"]["windows_11"].add(user)
                elif "windows10" in system_information_trimmed:
                    statistics["os"]["windows"]["windows_10"].add(user)
                elif "windows8.1" in system_information_trimmed:
                    statistics["os"]["windows"]["windows_8.1"].add(user)
                elif "windows8" in system_information_trimmed:
                    statistics["os"]["windows"]["windows_8"].add(user)
                elif "windows7" in system_information_trimmed:
                    statistics["os"]["windows"]["windows_7"].add(user)
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
                elif (
                    "arch" in system_information_trimmed
                    or "manjaro" in system_information_trimmed
                    or "endeavor" in system_information_trimmed
                    or "endeavour" in system_information_trimmed
                ):
                    statistics["os"]["linux"]["arch"].add(user)
                elif "linux" in system_information_trimmed:
                    statistics["os"]["linux"]["unknown"].add(user)

                if (
                    "macos13" in system_information_trimmed
                    or "macosventura" in system_information_trimmed
                ):
                    statistics["os"]["macos"]["macos_13"].add(user)
                elif (
                    "macos12" in system_information_trimmed
                    or "macosmonterey" in system_information_trimmed
                ):
                    statistics["os"]["macos"]["macos_12"].add(user)
                elif (
                    "macos11" in system_information_trimmed
                    or "macosbigsur" in system_information_trimmed
                ):
                    statistics["os"]["macos"]["macos_11"].add(user)
                elif (
                    "macos10.15" in system_information_trimmed
                    or "macoscatalina" in system_information_trimmed
                ):
                    statistics["os"]["macos"]["macos_10.15"].add(user)
                elif (
                    "macos10.14" in system_information_trimmed
                    or "macosmojave" in system_information_trimmed
                ):
                    statistics["os"]["macos"]["macos_10.14"].add(user)
                elif (
                    "macos10.13" in system_information_trimmed
                    or "macoshighsierra" in system_information_trimmed
                ):
                    statistics["os"]["macos"]["macos_10.13"].add(user)
                elif (
                    "macos10.12" in system_information_trimmed
                    or "macossierra" in system_information_trimmed
                ):
                    statistics["os"]["macos"]["macos_10.12"].add(user)
                elif "macos" in system_information_trimmed:
                    statistics["os"]["macos"]["unknown"].add(user)

                if "android13" in system_information_trimmed:
                    statistics["os"]["android"]["android_13"].add(user)
                elif "android12" in system_information_trimmed:
                    statistics["os"]["android"]["android_12"].add(user)
                elif "android11" in system_information_trimmed:
                    statistics["os"]["android"]["android_11"].add(user)
                elif "android10" in system_information_trimmed:
                    statistics["os"]["android"]["android_10"].add(user)
                elif "android9" in system_information_trimmed:
                    statistics["os"]["android"]["android_9"].add(user)
                elif "android8" in system_information_trimmed:
                    statistics["os"]["android"]["android_8"].add(user)
                elif "android7" in system_information_trimmed:
                    statistics["os"]["android"]["android_7"].add(user)
                elif "android6" in system_information_trimmed:
                    statistics["os"]["android"]["android_6"].add(user)
                elif "android5" in system_information_trimmed:
                    statistics["os"]["android"]["android_5"].add(user)
                elif "android" in system_information_trimmed:
                    statistics["os"]["android"]["unknown"].add(user)

                if "ios17" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_17"].add(user)
                elif "ios16" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_16"].add(user)
                elif "ios15" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_15"].add(user)
                elif "ios14" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_14"].add(user)
                elif "ios13" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_13"].add(user)
                elif "ios12" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_12"].add(user)
                elif "ios11" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_11"].add(user)
                elif "ios10" in system_information_trimmed:
                    statistics["os"]["ios"]["ios_10"].add(user)
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

                # TODO: Add laptop and Celeron/Pentium Intel CPUs.
                # TODO: Add Passmark scores for CPUs and GPUs.
                # The Intel CPU detection considers -KS and -KF CPUs identical to -K,
                # and -F identical to not having any suffix. (The -F suffix denotes a non-functional IGP.)
                if (
                    "i913900k" in system_information_trimmed
                    or "core13900k" in system_information_trimmed
                    or "intel13900k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["24_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"][">60000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"][">4500"].add(user)
                elif (
                    "i913900" in system_information_trimmed
                    or "core13900" in system_information_trimmed
                    or "intel13900" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["24_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["40000-50000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i713700k" in system_information_trimmed
                    or "core13700k" in system_information_trimmed
                    or "intel13700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["40000-50000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i713700" in system_information_trimmed
                    or "core13700" in system_information_trimmed
                    or "intel13700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i513600k" in system_information_trimmed
                    or "core13600k" in system_information_trimmed
                    or "intel13600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["14_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i513600" in system_information_trimmed
                    or "core13600" in system_information_trimmed
                    or "intel13600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["14_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i513500" in system_information_trimmed
                    or "core13500" in system_information_trimmed
                    or "intel13500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["14_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i513400" in system_information_trimmed
                    or "core13400" in system_information_trimmed
                    or "intel13400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["10_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i313100" in system_information_trimmed
                    or "core13100" in system_information_trimmed
                    or "intel13100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["raptor_lake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i912900k" in system_information_trimmed
                    or "core12900k" in system_information_trimmed
                    or "intel12900k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["40000-50000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i912900" in system_information_trimmed
                    or "core12900" in system_information_trimmed
                    or "intel12900" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i712700k" in system_information_trimmed
                    or "core12700k" in system_information_trimmed
                    or "intel12700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "i712700" in system_information_trimmed
                    or "core12700" in system_information_trimmed
                    or "intel12700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i512600k" in system_information_trimmed
                    or "core12600k" in system_information_trimmed
                    or "intel12600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["10_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i512600" in system_information_trimmed
                    or "core12600" in system_information_trimmed
                    or "intel12600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i512500" in system_information_trimmed
                    or "core12500" in system_information_trimmed
                    or "intel12500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i512400" in system_information_trimmed
                    or "core12400" in system_information_trimmed
                    or "intel12400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i312300" in system_information_trimmed
                    or "core12300" in system_information_trimmed
                    or "intel12300" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i312100" in system_information_trimmed
                    or "core12100" in system_information_trimmed
                    or "intel12100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["alder_lake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i911900k" in system_information_trimmed
                    or "core11900k" in system_information_trimmed
                    or "intel11900k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "i911900" in system_information_trimmed
                    or "core11900" in system_information_trimmed
                    or "intel11900" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i711700k" in system_information_trimmed
                    or "core11700k" in system_information_trimmed
                    or "intel11700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i711700" in system_information_trimmed
                    or "core11700" in system_information_trimmed
                    or "intel11700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i511600k" in system_information_trimmed
                    or "core11600k" in system_information_trimmed
                    or "intel11600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i511600" in system_information_trimmed
                    or "core11600" in system_information_trimmed
                    or "intel11600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i511500" in system_information_trimmed
                    or "core11500" in system_information_trimmed
                    or "intel11500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i511400" in system_information_trimmed
                    or "core11400" in system_information_trimmed
                    or "intel11400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["rocket_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i910900k" in system_information_trimmed
                    or "core10900k" in system_information_trimmed
                    or "intel10900k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["10_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i910900" in system_information_trimmed
                    or "core10900" in system_information_trimmed
                    or "intel10900" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["10_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "i710700k" in system_information_trimmed
                    or "core10700k" in system_information_trimmed
                    or "intel10700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i710700" in system_information_trimmed
                    or "core10700" in system_information_trimmed
                    or "intel10700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i510600k" in system_information_trimmed
                    or "core10600k" in system_information_trimmed
                    or "intel10600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i510600" in system_information_trimmed
                    or "core10600" in system_information_trimmed
                    or "intel10600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i510500" in system_information_trimmed
                    or "core10500" in system_information_trimmed
                    or "intel10500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i510400" in system_information_trimmed
                    or "core10400" in system_information_trimmed
                    or "intel10400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i310300" in system_information_trimmed
                    or "core10300" in system_information_trimmed
                    or "intel10300" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i310100" in system_information_trimmed
                    or "core10100" in system_information_trimmed
                    or "intel10100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["comet_lake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i99900k" in system_information_trimmed
                    or "core9900k" in system_information_trimmed
                    or "intel9900k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i99900" in system_information_trimmed
                    or "core9900" in system_information_trimmed
                    or "intel9900" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i79700k" in system_information_trimmed
                    or "core9700k" in system_information_trimmed
                    or "intel9700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i79700" in system_information_trimmed
                    or "core9700" in system_information_trimmed
                    or "intel9700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i59600k" in system_information_trimmed
                    or "core9600k" in system_information_trimmed
                    or "intel9600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i59600" in system_information_trimmed
                    or "core9600" in system_information_trimmed
                    or "intel9600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i59500" in system_information_trimmed
                    or "core9500" in system_information_trimmed
                    or "intel9500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i59400" in system_information_trimmed
                    or "core9400" in system_information_trimmed
                    or "intel9400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i39350k" in system_information_trimmed
                    or "core9350k" in system_information_trimmed
                    or "intel9350k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i39300" in system_information_trimmed
                    or "core9300" in system_information_trimmed
                    or "intel9300" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i39100" in system_information_trimmed
                    or "core9100" in system_information_trimmed
                    or "intel9100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake_refresh"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i78700k" in system_information_trimmed
                    or "core8700k" in system_information_trimmed
                    or "intel8700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i78700" in system_information_trimmed
                    or "core8700" in system_information_trimmed
                    or "intel8700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i78086k" in system_information_trimmed
                    or "core8086k" in system_information_trimmed
                    or "intel8086k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i58600k" in system_information_trimmed
                    or "core8600k" in system_information_trimmed
                    or "intel8600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i58500" in system_information_trimmed
                    or "core8500" in system_information_trimmed
                    or "intel8500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i58400" in system_information_trimmed
                    or "core8400" in system_information_trimmed
                    or "intel8400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i38350k" in system_information_trimmed
                    or "core8350k" in system_information_trimmed
                    or "intel8350k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i38100" in system_information_trimmed
                    or "core8100" in system_information_trimmed
                    or "intel8100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["coffee_lake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i77700k" in system_information_trimmed
                    or "core7700k" in system_information_trimmed
                    or "intel7700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i77700" in system_information_trimmed
                    or "core7700" in system_information_trimmed
                    or "intel7700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i57600k" in system_information_trimmed
                    or "core7600k" in system_information_trimmed
                    or "intel7600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i57600" in system_information_trimmed
                    or "core7600" in system_information_trimmed
                    or "intel7600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i57500" in system_information_trimmed
                    or "core7500" in system_information_trimmed
                    or "intel7500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i57400" in system_information_trimmed
                    or "core7400" in system_information_trimmed
                    or "intel7400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i37350k" in system_information_trimmed
                    or "core7350k" in system_information_trimmed
                    or "intel7350k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i37300" in system_information_trimmed
                    or "core7300" in system_information_trimmed
                    or "intel7300" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i37100" in system_information_trimmed
                    or "core7100" in system_information_trimmed
                    or "intel7100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i76700k" in system_information_trimmed
                    or "core6700k" in system_information_trimmed
                    or "intel6700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "i76700" in system_information_trimmed
                    or "core6700" in system_information_trimmed
                    or "intel6700" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i56600k" in system_information_trimmed
                    or "core6600k" in system_information_trimmed
                    or "intel6600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i56600" in system_information_trimmed
                    or "core6600" in system_information_trimmed
                    or "intel6600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i56500" in system_information_trimmed
                    or "core6500" in system_information_trimmed
                    or "intel6500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i56400" in system_information_trimmed
                    or "core6400" in system_information_trimmed
                    or "intel6400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i36300" in system_information_trimmed
                    or "core6300" in system_information_trimmed
                    or "intel6300" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i36100" in system_information_trimmed
                    or "core6100" in system_information_trimmed
                    or "intel6100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["skylake"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i74790k" in system_information_trimmed
                    or "core4790k" in system_information_trimmed
                    or "intel4790k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i74790" in system_information_trimmed
                    or "core4790" in system_information_trimmed
                    or "intel4790" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i74770k" in system_information_trimmed
                    or "core4770k" in system_information_trimmed
                    or "intel4770k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i74770" in system_information_trimmed
                    or "core4770" in system_information_trimmed
                    or "intel4770" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i54670k" in system_information_trimmed
                    or "core4670k" in system_information_trimmed
                    or "intel4670k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i54670" in system_information_trimmed
                    or "core4670" in system_information_trimmed
                    or "intel4670" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i54590" in system_information_trimmed
                    or "core4590" in system_information_trimmed
                    or "intel4590" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i54570" in system_information_trimmed
                    or "core4570" in system_information_trimmed
                    or "intel4570" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i54460" in system_information_trimmed
                    or "core4460" in system_information_trimmed
                    or "intel4460" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i54440" in system_information_trimmed
                    or "core4440" in system_information_trimmed
                    or "intel4440" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i54430" in system_information_trimmed
                    or "core4430" in system_information_trimmed
                    or "intel4430" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i34370" in system_information_trimmed
                    or "core4370" in system_information_trimmed
                    or "intel4370" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i34360" in system_information_trimmed
                    or "core4360" in system_information_trimmed
                    or "intel4360" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i34350" in system_information_trimmed
                    or "core4350" in system_information_trimmed
                    or "intel4350" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i34340" in system_information_trimmed
                    or "core4340" in system_information_trimmed
                    or "intel4340" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i34330" in system_information_trimmed
                    or "core4330" in system_information_trimmed
                    or "intel4330" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i34170" in system_information_trimmed
                    or "core4170" in system_information_trimmed
                    or "intel4170" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i34160" in system_information_trimmed
                    or "core4160" in system_information_trimmed
                    or "intel4160" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i34150" in system_information_trimmed
                    or "core4150" in system_information_trimmed
                    or "intel4150" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i34130" in system_information_trimmed
                    or "core4130" in system_information_trimmed
                    or "intel4130" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["haswell"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i73770k" in system_information_trimmed
                    or "core3770k" in system_information_trimmed
                    or "intel3770k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i73770" in system_information_trimmed
                    or "core3770" in system_information_trimmed
                    or "intel3770" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i53570k" in system_information_trimmed
                    or "core3570k" in system_information_trimmed
                    or "intel3570k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i53570" in system_information_trimmed
                    or "core3570" in system_information_trimmed
                    or "intel3570" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "i53550" in system_information_trimmed
                    or "core3550" in system_information_trimmed
                    or "intel3550" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i53470" in system_information_trimmed
                    or "core3470" in system_information_trimmed
                    or "intel3470" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i53450" in system_information_trimmed
                    or "core3450" in system_information_trimmed
                    or "intel3450" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i53340" in system_information_trimmed
                    or "core3340" in system_information_trimmed
                    or "intel3340" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i53330" in system_information_trimmed
                    or "core3330" in system_information_trimmed
                    or "intel3330" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i33250" in system_information_trimmed
                    or "core3250" in system_information_trimmed
                    or "intel3250" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i33240" in system_information_trimmed
                    or "core3240" in system_information_trimmed
                    or "intel3240" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i33220" in system_information_trimmed
                    or "core3220" in system_information_trimmed
                    or "intel3220" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i33210" in system_information_trimmed
                    or "core3210" in system_information_trimmed
                    or "intel3210" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["ivy_bridge"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i72700k" in system_information_trimmed
                    or "core2700k" in system_information_trimmed
                    or "intel2700k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i72600k" in system_information_trimmed
                    or "core2600k" in system_information_trimmed
                    or "intel2600k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i72600" in system_information_trimmed
                    or "core2600" in system_information_trimmed
                    or "intel2600" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i52500k" in system_information_trimmed
                    or "core2500k" in system_information_trimmed
                    or "intel2500k" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i52500" in system_information_trimmed
                    or "core2500" in system_information_trimmed
                    or "intel2500" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i52400" in system_information_trimmed
                    or "core2400" in system_information_trimmed
                    or "intel2400" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i52300" in system_information_trimmed
                    or "core2300" in system_information_trimmed
                    or "intel2300" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["<1500"].add(user)
                elif (
                    "i32130" in system_information_trimmed
                    or "core2130" in system_information_trimmed
                    or "intel2130" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i32120" in system_information_trimmed
                    or "core2120" in system_information_trimmed
                    or "intel2120" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "i32100" in system_information_trimmed
                    or "core2100" in system_information_trimmed
                    or "intel2100" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["sandy_bridge"].add(user)
                    statistics["cpu_core_count"]["2_cores"].add(user)
                    statistics["cpu_x86_features"]["avx"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["<5000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["<1500"].add(user)
                elif (
                    "intelcore" in system_information_trimmed
                    or "inteli" in system_information_trimmed
                    or "celeron" in system_information_trimmed
                    or "pentium" in system_information_trimmed
                    or "xeon" in system_information_trimmed
                ):
                    statistics["cpu"]["intel"]["unknown"].add(user)

                # TODO: Add laptop AMD CPUs, Athlons and Threadrippers.
                # NOTE: Unlike Intel CPUs, detection does not allow "amd<number>" as this syntax is used for GPUs instead.
                #       There would be some ambiguities otherwise, such as Ryzen 5 7600 versus Radeon RX 7600.
                if (
                    "ryzen97950x3d" in system_information_trimmed
                    or "ryzen7950x3d" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"][">60000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen97950x" in system_information_trimmed
                    or "ryzen7950x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"][">60000"].add(user)
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen97900x3d" in system_information_trimmed
                    or "ryzen7900x3d" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["50000-60000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen97900x" in system_information_trimmed
                    or "ryzen7900x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["50000-60000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen97900" in system_information_trimmed
                    or "ryzen7900" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["40000-50000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen77800x3d" in system_information_trimmed
                    or "ryzen7800x3d" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3500-4000"].add(
                        user
                    )
                elif (
                    "ryzen77700x" in system_information_trimmed
                    or "ryzen7700x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen77700" in system_information_trimmed
                    or "ryzen7700" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen57600x" in system_information_trimmed
                    or "ryzen7600x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen57600" in system_information_trimmed
                    or "ryzen7600" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen4"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx512"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["4000-4500"].add(
                        user
                    )
                elif (
                    "ryzen95950x" in system_information_trimmed
                    or "ryzen5950x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["40000-50000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen95900x" in system_information_trimmed
                    or "ryzen5900x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen95900" in system_information_trimmed
                    or "ryzen5900" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen75800x3d" in system_information_trimmed
                    or "ryzen5800x3d" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen75800x" in system_information_trimmed
                    or "ryzen5800x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen75800" in system_information_trimmed
                    or "ryzen5800" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen75700x" in system_information_trimmed
                    or "ryzen5700x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen75700g" in system_information_trimmed
                    or "ryzen5700g" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen75700" in system_information_trimmed
                    or "ryzen5700" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen55600x" in system_information_trimmed
                    or "ryzen5600x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen55600g" in system_information_trimmed
                    or "ryzen5600g" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen55600" in system_information_trimmed
                    or "ryzen5600" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen3"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen55500" in system_information_trimmed
                    or "ryzen5500" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["3000-3500"].add(
                        user
                    )
                elif (
                    "ryzen93950x" in system_information_trimmed
                    or "ryzen3950x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["16_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen93900x" in system_information_trimmed
                    or "ryzen3900x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen93900" in system_information_trimmed
                    or "ryzen3900" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["12_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["30000-40000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen73800x" in system_information_trimmed
                    or "ryzen3800x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen73700x" in system_information_trimmed
                    or "ryzen3700x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["20000-30000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen53600x" in system_information_trimmed
                    or "ryzen3600x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen53600" in system_information_trimmed
                    or "ryzen3600" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen33300x" in system_information_trimmed
                    or "ryzen3300x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen2"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2500-3000"].add(
                        user
                    )
                elif (
                    "ryzen72700x" in system_information_trimmed
                    or "ryzen2700x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen72700" in system_information_trimmed
                    or "ryzen2700" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen52600x" in system_information_trimmed
                    or "ryzen2600x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen52600" in system_information_trimmed
                    or "ryzen2600" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen52500x" in system_information_trimmed
                    or "ryzen2500x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen52400g" in system_information_trimmed
                    or "ryzen2400g" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen32300x" in system_information_trimmed
                    or "ryzen2300x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen32200g" in system_information_trimmed
                    or "ryzen2200g" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen71800x" in system_information_trimmed
                    or "ryzen1800x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen71700x" in system_information_trimmed
                    or "ryzen1700x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen71700" in system_information_trimmed
                    or "ryzen1700" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["8_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen51600x" in system_information_trimmed
                    or "ryzen1600x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen51600" in system_information_trimmed
                    or "ryzen1600" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["6_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["10000-20000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen51500x" in system_information_trimmed
                    or "ryzen1500x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen51400" in system_information_trimmed
                    or "ryzen1400" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "ryzen31300x" in system_information_trimmed
                    or "ryzen1300x" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["2000-2500"].add(
                        user
                    )
                elif (
                    "ryzen31200" in system_information_trimmed
                    or "ryzen1200" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["zen+"].add(user)
                    statistics["cpu_core_count"]["4_cores"].add(user)
                    statistics["cpu_x86_features"]["avx2"].add(user)
                    statistics["cpu_passmark_score"]["multi_thread"]["5000-10000"].add(
                        user
                    )
                    statistics["cpu_passmark_score"]["single_thread"]["1500-2000"].add(
                        user
                    )
                elif (
                    "ryzen" in system_information_trimmed
                    or "fx" in system_information_trimmed
                    or "athlon" in system_information_trimmed
                    or "phenom" in system_information_trimmed
                    or "threadripper" in system_information_trimmed
                    or "epyc" in system_information_trimmed
                ):
                    statistics["cpu"]["amd"]["unknown"].add(user)

                # RTX models only scan for "tx" to allow for misspellings (e.g. "GTX 2070").
                # NOTE: In this scanning, laptop GPUs are only separated from desktop GPUs since Ampere.
                #       This may not be reliable in all cases if the user has removed the "Mobile"
                #       or "Laptop" suffix from the model name.
                if (
                    "tx4090" in system_information_trimmed
                    or "geforce4090" in system_information_trimmed
                    or "nvidia4090" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["24_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"][">30000"].add(user)
                elif (
                    "4090laptop" in system_information_trimmed
                    or "4090mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["16_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "tx4080" in system_information_trimmed
                    or "geforce4080" in system_information_trimmed
                    or "nvidia4080" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["16_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"][">30000"].add(user)
                elif (
                    "4080laptop" in system_information_trimmed
                    or "4080mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["12_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "tx4070ti" in system_information_trimmed
                    or "geforce4070ti" in system_information_trimmed
                    or "nvidia4070ti" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["12_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"][">30000"].add(user)
                elif (
                    "tx4070" in system_information_trimmed
                    or "geforce4070" in system_information_trimmed
                    or "nvidia4070" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["12_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "4070laptop" in system_information_trimmed
                    or "4070mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx4060ti" in system_information_trimmed
                    or "geforce4060ti" in system_information_trimmed
                    or "nvidia4060ti" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    # Assume 8 GB variant, which is much more widespread than the 16 GB one.
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
                elif (
                    "tx4060" in system_information_trimmed
                    or "geforce4060" in system_information_trimmed
                    or "nvidia4060" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "4060laptop" in system_information_trimmed
                    or "4060mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "4050laptop" in system_information_trimmed
                    or "4050mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ada_lovelace"].add(user)
                    statistics["gpu_vram"]["6_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx3090ti" in system_information_trimmed
                    or "geforce3090ti" in system_information_trimmed
                    or "nvidia3090ti" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["24_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "tx3090" in system_information_trimmed
                    or "geforce3090" in system_information_trimmed
                    or "nvidia3090" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["24_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "tx3080ti" in system_information_trimmed
                    or "geforce3080ti" in system_information_trimmed
                    or "nvidia3080ti" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["10_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "3080tilaptop" in system_information_trimmed
                    or "3080timobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["16_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
                elif (
                    "tx3080" in system_information_trimmed
                    or "geforce3080" in system_information_trimmed
                    or "nvidia3080" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    # Assume 8 GB variant, which is much more widespread than the 16 GB one.
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "3080laptop" in system_information_trimmed
                    or "3080mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["6_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx3070ti" in system_information_trimmed
                    or "geforce3070ti" in system_information_trimmed
                    or "nvidia3070ti" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
                elif (
                    "3070tilaptop" in system_information_trimmed
                    or "3070timobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx3070" in system_information_trimmed
                    or "geforce3070" in system_information_trimmed
                    or "nvidia3070" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
                elif (
                    "3070laptop" in system_information_trimmed
                    or "3070mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx3060ti" in system_information_trimmed
                    or "geforce3060ti" in system_information_trimmed
                    or "nvidia3060ti" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
                elif (
                    "tx3060" in system_information_trimmed
                    or "geforce3060" in system_information_trimmed
                    or "nvidia3060" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    # Assume 12 GB variant, which is much more widespread than the 8 GB one.
                    statistics["gpu_vram"]["12_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "3060laptop" in system_information_trimmed
                    or "3060mobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["6_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
                elif (
                    "3050tilaptop" in system_information_trimmed
                    or "3050timobile" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["6_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
                elif (
                    "tx3050" in system_information_trimmed
                    or "geforce3050" in system_information_trimmed
                    or "nvidia3050" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_ampere"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
                elif (
                    "tx2080ti" in system_information_trimmed
                    or "geforce2080ti" in system_information_trimmed
                    or "nvidia2080ti" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                    statistics["gpu_vram"]["11_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
                elif (
                    "tx2080super" in system_information_trimmed
                    or "geforce2080super" in system_information_trimmed
                    or "nvidia2080super" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                    statistics["gpu_vram"]["11_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx2080" in system_information_trimmed
                    or "geforce2080" in system_information_trimmed
                    or "nvidia2080" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx2070super" in system_information_trimmed
                    or "geforce2070super" in system_information_trimmed
                    or "nvidia2070super" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx2070" in system_information_trimmed
                    or "geforce2070" in system_information_trimmed
                    or "nvidia2070" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx2060super" in system_information_trimmed
                    or "geforce2060super" in system_information_trimmed
                    or "nvidia2060super" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif (
                    "tx2060" in system_information_trimmed
                    or "geforce2060" in system_information_trimmed
                    or "nvidia2060" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_turing"].add(user)
                    # Assume 6 GB variant, which is much more widespread than the 12 GB one.
                    statistics["gpu_vram"]["6_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    # 6 GB variant is slower than the 12 GB one;
                    # the 12 GB one is in the 15000-20000 performance bracket.
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
                elif (
                    "gtx690" in system_information_trimmed
                    or "geforce690" in system_information_trimmed
                    or "nvidia690" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_kepler"].add(user)
                    # Dual-GPU card; since Godot doesn't support multi-GPU,
                    # only account for the VRAM and performance of a single GPU.
                    statistics["gpu_vram"]["2_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif (
                    "gtx590" in system_information_trimmed
                    or "geforce590" in system_information_trimmed
                    or "nvidia590" in system_information_trimmed
                ):
                    statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                    # Dual-GPU card; since Godot doesn't support multi-GPU,
                    # only account for the VRAM and performance of a single GPU.
                    # 1.5 GB of VRAM per GPU; round down to 1 GB.
                    statistics["gpu_vram"]["1_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif (
                    "gt710" in system_information_trimmed
                    or "geforce710" in system_information_trimmed
                    or "nvidia710" in system_information_trimmed
                ):
                    # The GeForce GT 710 is a Fermi GPU despite being in the 700 series.
                    statistics["gpu"]["nvidia"]["dedicated_fermi"].add(user)
                    statistics["gpu_vram"]["12_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif (
                    "nvidia" in system_information_trimmed
                    or "quadro" in system_information_trimmed
                    or "tesla" in system_information_trimmed
                ):
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
                    statistics["gpu_passmark_score"][">30000"].add(user)
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
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
                elif (
                    "rx7600" in system_information_trimmed
                    or "radeon7600" in system_information_trimmed
                    or "amd7600" in system_information_trimmed
                ):
                    statistics["gpu"]["amd"]["dedicated_rdna3"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
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
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
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
                    statistics["gpu_passmark_score"]["25000-30000"].add(user)
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
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
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
                    statistics["gpu_passmark_score"]["20000-25000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
                elif (
                    "rx5600" in system_information_trimmed
                    or "radeon5600" in system_information_trimmed
                    or "amd5600" in system_information_trimmed
                ):
                    statistics["gpu"]["amd"]["dedicated_rdna1"].add(user)
                    statistics["gpu_vram"]["6_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
                elif (
                    "rx5500" in system_information_trimmed
                    or "radeon5500" in system_information_trimmed
                    or "amd5500" in system_information_trimmed
                ):
                    statistics["gpu"]["amd"]["dedicated_rdna1"].add(user)
                    statistics["gpu_vram"]["4_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
                elif "radeonvii" in system_information_trimmed:
                    statistics["gpu"]["amd"]["dedicated_gcn5.0"].add(user)
                    statistics["gpu_vram"]["4_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["15000-20000"].add(user)
                elif "vega64" in system_information_trimmed:
                    statistics["gpu"]["amd"]["dedicated_gcn5.0"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["10000-15000"].add(user)
                elif "vega56" in system_information_trimmed:
                    statistics["gpu"]["amd"]["dedicated_gcn5.0"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["no"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["10000-25000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
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
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
                elif (
                    "radeon" in system_information_trimmed
                    or "firepro" in system_information_trimmed
                ):
                    statistics["gpu"]["amd"]["unknown"].add(user)

                if "a780" in system_information_trimmed:
                    statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                    statistics["gpu_vram"]["16_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
                elif "a770" in system_information_trimmed:
                    statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                    statistics["gpu_vram"]["16_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
                elif "a750" in system_information_trimmed:
                    statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
                elif "a580" in system_information_trimmed:
                    statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                    statistics["gpu_vram"]["8_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["5000-10000"].add(user)
                elif "a380" in system_information_trimmed:
                    statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                    statistics["gpu_vram"]["6_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
                elif "a350" in system_information_trimmed:
                    statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                    statistics["gpu_vram"]["4_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
                elif "a310" in system_information_trimmed:
                    statistics["gpu"]["intel"]["dedicated_arc_alchemist"].add(user)
                    statistics["gpu_vram"]["4_gb"].add(user)
                    statistics["gpu_raytracing"]["dedicated"]["yes"].add(user)
                    statistics["gpu_vrs"]["dedicated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["dedicated"]["yes"].add(user)
                    statistics["gpu_passmark_score"]["2500-5000"].add(user)
                elif "uhd770" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd750" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd730" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd710" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen12"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["yes"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "irisplus655" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "irisplus645" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd630" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd620" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd617" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd615" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "uhd610" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "irisplus650" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "irisplus640" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd630" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd620" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd615" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd610" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif (
                    "iris580" in system_information_trimmed
                ):  # Originally "irispro580", but we stripped "pro" to make parsing Ryzen PRO easier.
                    statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "iris550" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "iris540" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd530" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd520" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd515" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd510" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen9"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif (
                    "iris6200" in system_information_trimmed
                ):  # Originally "irispro6200", but we stripped "pro" to make parsing Ryzen PRO easier.
                    statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "iris6100" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd6000" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd5600" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd5500" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd5300" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen8"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif (
                    "iris5200" in system_information_trimmed
                ):  # Originally "irispro5200", but we stripped "pro" to make parsing Ryzen PRO easier.
                    statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "iris5100" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd5000" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd4600" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd4400" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd4200" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen7.5"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd4000" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen7"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd2500" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen7"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
                elif "hd3000" in system_information_trimmed:
                    statistics["gpu"]["intel"]["integrated_gen6"].add(user)
                    statistics["gpu_raytracing"]["integrated"]["no"].add(user)
                    statistics["gpu_vrs"]["integrated"]["no"].add(user)
                    statistics["gpu_mesh_shaders"]["integrated"]["no"].add(user)
                    statistics["gpu_passmark_score"]["<2500"].add(user)
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
                    # Assume this is a slow GPU, as even high-end Iris Xe barely scratches
                    # the 2500 points mark as of June 2023.
                    statistics["gpu_passmark_score"]["<2500"].add(user)

    statistics["num_reports"] = len(user_system_infos)
    statistics["first_report_date"] = first_report_date
    statistics["last_report_date"] = last_report_date
    print(f"Number of scannable reports: {statistics['num_reports']}")

    output_path: Final = "statistics.json"
    with open(output_path, "w") as out_file:
        # Serialize Python sets as their length as an integer, since we only need to know how many users
        # match each metric (and not who exactly).
        def set_default(obj: object) -> int:
            if isinstance(obj, set):
                return len(obj)
            raise TypeError

        json.dump(statistics, out_file, default=set_default)

    print(f"Wrote statistics to: {output_path}")


if __name__ == "__main__":
    main()
