/** battle.js getHpColor と同じ段階色 */
export function getHpColor(percent: number): string {
    if (percent >= 81) return "rgb(73, 254, 73)";
    if (percent >= 66) return "rgb(200, 254, 73)";
    if (percent >= 50) return "rgb(251, 254, 73)";
    if (percent >= 31) return "rgb(254, 191, 73)";
    return "rgb(255, 0, 0)";
}

export function resolveAssetPath(path: string): string {
    if (path.startsWith("/")) return path;
    if (path.startsWith("game/")) return `/${path}`;
    return `/game/${path}`;
}

export function enemyImageSrc(imageUrl: string | undefined): string {
    if (!imageUrl) return "";
    return resolveAssetPath(imageUrl);
}

export function stageBackgroundSrc(backgroundImage: string): string {
    return `/game/img/背景/${backgroundImage}`;
}
