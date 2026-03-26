export const getCookie = (name: string) => {
    const cookies = document.cookie.split(";");
    for(const cookie of cookies) {
        const c = cookie.trim();
        if (c.startsWith(name + "=")) {
            return decodeURIComponent(c.substring(name.length + 1));
        }
    }
    return "";
}

export const apiGet = async(path: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`, {
        credentials: 'include',
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

export const apiPost = async(path: string, data: Record<string, string>) => {
    const formData = new FormData();
    formData.append("name", data.name);
    formData.append("job", data.job);

    const csrfToken = getCookie('csrftoken');
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`, {
        credentials: 'include',
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
        body: formData,
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}