export default {
  async fetch(request) {
    const url = new URL(request.url);
    // ЗДЕСЬ ВАЖНО: укажите АДРЕС ВАШЕГО ПРОЕКТА на Hugging Face
    const targetUrl = `https://dkvhug-botolink.hf.space${url.pathname}${url.search}`;

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });

    return response;
  }
}
