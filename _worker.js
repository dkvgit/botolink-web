export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // ВАШ АДРЕС НА HUGGING FACE
    const targetUrl = 'https://dkvhug-botolink.hf.space' + url.pathname + url.search;
    
    // Важно: Hugging Face не принимает HEAD-запросы, конвертируем в GET
    const method = request.method === 'HEAD' ? 'GET' : request.method;
    
    const newRequest = new Request(targetUrl, {
      method: method,
      headers: request.headers,
      body: request.method === 'HEAD' ? null : request.body,
    });
    
    const response = await fetch(newRequest);
    const newHeaders = new Headers(response.headers);
    newHeaders.set('Access-Control-Allow-Origin', '*');
    
    return new Response(
      request.method === 'HEAD' ? null : response.body,
      {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      }
    );
  }
}
