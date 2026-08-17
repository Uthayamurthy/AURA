function parseServerDate(timestamp: string): Date {
    const normalized = timestamp.includes('T')
        ? timestamp
        : timestamp.replace(' ', 'T');
    const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized);

    return new Date(hasTimezone ? normalized : `${normalized}Z`);
}

const IST_TIME_ZONE = 'Asia/Kolkata';

export function formatIstTime(timestamp: string, includeSeconds = true): string {
    return new Intl.DateTimeFormat('en-IN', {
        timeZone: IST_TIME_ZONE,
        hour: 'numeric',
        minute: '2-digit',
        second: includeSeconds ? '2-digit' : undefined,
        hour12: true,
        timeZoneName: 'short',
    }).format(parseServerDate(timestamp));
}

export function formatIstDate(timestamp: string, long = false): string {
    return new Intl.DateTimeFormat('en-IN', {
        timeZone: IST_TIME_ZONE,
        day: 'numeric',
        month: long ? 'long' : 'short',
        year: 'numeric',
    }).format(parseServerDate(timestamp));
}

function istParts(timestamp: string): Record<string, string> {
    return Object.fromEntries(
        new Intl.DateTimeFormat('en-GB', {
            timeZone: IST_TIME_ZONE,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hourCycle: 'h23',
        }).formatToParts(parseServerDate(timestamp)).map(({ type, value }) => [type, value])
    );
}

export function formatIstDateKey(timestamp: string): string {
    const parts = istParts(timestamp);
    return `${parts.year}-${parts.month}-${parts.day}`;
}

export function formatIstCsvTimestamp(timestamp: string): string {
    const parts = istParts(timestamp);
    return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second} IST`;
}
