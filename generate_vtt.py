#!/usr/bin/env python3

def numberToMillis(n: int) -> int:
    return 1000 * n // 3

def formatMillis(t: int) -> str:
    t, millis = divmod(t, 1000)
    t, seconds = divmod(t, 60)
    hours, minutes = divmod(t, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"

def formatRangeForNumber(n: int) -> str:
    start = formatMillis(numberToMillis(n))
    end = formatMillis(numberToMillis(n + 1))
    return f"{start} --> {end}"

def cueForNumber(n: int) -> str:
    return f"{formatRangeForNumber(n)}\nThe screen should show number {n+1}."

def genVtt() -> str:
    return "WEBVTT\n\n" + "\n\n".join(
        cueForNumber(i)
        for i in range(30)
    )

if __name__ == "__main__":
    print(genVtt())