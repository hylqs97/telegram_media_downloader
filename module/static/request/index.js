var request = (url, type = 'get', data = {}) => {
    const $ = layui.$
    const method = String(type || 'get').toLowerCase()

    return new Promise((resolve, reject) => {
        $.ajax({
            url,
            type: method,
            data,
            dataType: 'json',
            timeout: 60 * 1000,
            contentType: method === 'get' ? undefined : 'application/x-www-form-urlencoded; charset=UTF-8',
            success: (res) => {
                resolve(res)
            },
            error: (err) => {
                reject(err)
            }
        })
    })
}
