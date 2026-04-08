# -*- coding: utf-8 -*-

import re


def extract_exit_ip(payload):
    if not payload:
        return ""

    if isinstance(payload, dict):
        origin = payload.get("origin", "")
    else:
        origin = payload

    if not origin:
        return ""

    if isinstance(origin, list):
        origin = ",".join(origin)

    for item in str(origin).split(","):
        ip = item.strip()
        if ip:
            matched = re.search(r"\d{1,3}(?:\.\d{1,3}){3}", ip)
            if matched:
                return matched.group(0)
            return ip
    return ""


def merge_proxy_state(current_proxy, stored_proxy):
    if not stored_proxy:
        return current_proxy

    for source in stored_proxy.source.split('/'):
        current_proxy.add_source(source)

    current_proxy.fail_count = stored_proxy.fail_count
    current_proxy.check_count = stored_proxy.check_count
    current_proxy.last_status = stored_proxy.last_status
    current_proxy.last_time = stored_proxy.last_time
    current_proxy.https = stored_proxy.https
    current_proxy.region = stored_proxy.region
    current_proxy.score = stored_proxy.score
    current_proxy.success_streak = stored_proxy.success_streak
    current_proxy.http_success_streak = stored_proxy.http_success_streak
    current_proxy.https_success_streak = stored_proxy.https_success_streak
    current_proxy.http_last_status = stored_proxy.http_last_status
    current_proxy.https_last_status = stored_proxy.https_last_status
    current_proxy.exit_ip = stored_proxy.exit_ip
    current_proxy.qualified = stored_proxy.qualified
    return current_proxy


def should_qualify(proxy, qualify_success_streak):
    if proxy.http_success_streak < qualify_success_streak:
        return False
    if proxy.https:
        return proxy.https_success_streak >= qualify_success_streak
    return True


def apply_validation_result(proxy, http_ok, https_ok, exit_ip, check_time, region, qualify_success_streak):
    proxy.check_count += 1
    proxy.last_time = check_time
    proxy.last_status = bool(http_ok)
    proxy.http_last_status = bool(http_ok)
    proxy.https_last_status = bool(https_ok) if http_ok else False

    if http_ok:
        proxy.success_streak += 1
        proxy.http_success_streak += 1
        proxy.score += 2
        proxy.fail_count = max(proxy.fail_count - 1, 0)
        if exit_ip:
            proxy.exit_ip = exit_ip
        if region:
            proxy.region = region

        if https_ok:
            proxy.https = True
            proxy.https_success_streak += 1
            proxy.score += 1
        else:
            proxy.https = False
            proxy.https_success_streak = 0
    else:
        proxy.fail_count += 1
        proxy.success_streak = 0
        proxy.http_success_streak = 0
        proxy.https_success_streak = 0
        proxy.https = False
        proxy.score = max(proxy.score - 3, 0)

    proxy.qualified = should_qualify(proxy, qualify_success_streak)
    return proxy


def is_better_proxy(current_proxy, stored_proxy):
    current_rank = (
        1 if current_proxy.qualified else 0,
        current_proxy.score,
        current_proxy.success_streak,
        1 if current_proxy.https else 0,
        -current_proxy.fail_count,
        current_proxy.check_count,
    )
    stored_rank = (
        1 if stored_proxy.qualified else 0,
        stored_proxy.score,
        stored_proxy.success_streak,
        1 if stored_proxy.https else 0,
        -stored_proxy.fail_count,
        stored_proxy.check_count,
    )
    return current_rank >= stored_rank
