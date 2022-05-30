const {
    REACT_APP_HOMEPAGE,
    REACT_APP_SERVER_URL
} = process.env;

/**
 * 
 * @param {string} endpoint - An endpoint for the flask server (e.g. `"/get/modulenames"`).
 * @param {string} contentType - The value to be used for the `"Content-Type"` key in the `headers` key-value object.
 * @param {string|null} body - The contents of the body of the request. Defaults to `null`, but if specified should be a `string` obtained from the `JSON.stringify` method.
 * @returns {string} Either the `Response.text()` if the `Response.statusText === "OK"` else the `Response.statusText`.
 */
async function handleFetch(endpoint, contentType, body = null) {

    let output;

    const response = await fetch(REACT_APP_SERVER_URL+endpoint, {
        method: "GET",
        headers: {"Content-Type": contentType}
    });

    if (response.statusText === "OK") {
        const data = await response.text();
        output = data;
    } else {
        output = response.statusText;
    }

    return output;
}

export default handleFetch;