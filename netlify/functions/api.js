// Netlify Function to proxy ALL API requests to Railway backend
exports.handler = async (event, context) => {
  const { path, httpMethod, headers, body, queryStringParameters } = event;
  
  // Extract the path after /.netlify/functions/api and prepend /api
  const apiPath = path.replace('/.netlify/functions/api', '') || '';
  const backendPath = `/api${apiPath}`;
  
  // Add query parameters if they exist
  const queryString = queryStringParameters 
    ? '?' + new URLSearchParams(queryStringParameters).toString()
    : '';
  
  const backendUrl = `https://wolfhunt-production.up.railway.app${backendPath}${queryString}`;
  
  console.log(`Proxying ${httpMethod} ${path} to ${backendUrl}`);
  
  // Handle CORS preflight
  if (httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Max-Age': '86400',
      },
      body: '',
    };
  }
  
  try {
    const fetchHeaders = {
      ...headers,
      'host': undefined, // Remove host header to avoid conflicts
      'x-forwarded-for': undefined, // Remove Netlify headers
      'x-forwarded-proto': undefined,
    };
    
    const response = await fetch(backendUrl, {
      method: httpMethod,
      headers: fetchHeaders,
      body: httpMethod !== 'GET' && httpMethod !== 'HEAD' ? body : undefined,
    });
    
    const responseBody = await response.text();
    const responseHeaders = {};
    
    // Copy important headers from backend response
    response.headers.forEach((value, key) => {
      if (['content-type', 'cache-control', 'etag'].includes(key.toLowerCase())) {
        responseHeaders[key] = value;
      }
    });
    
    return {
      statusCode: response.status,
      headers: {
        ...responseHeaders,
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      },
      body: responseBody,
    };
  } catch (error) {
    console.error('Proxy error:', error);
    return {
      statusCode: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        error: 'Proxy failed', 
        details: error.message,
        path: backendPath,
        url: backendUrl
      }),
    };
  }
};