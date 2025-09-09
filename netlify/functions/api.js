// Netlify Function to proxy API requests to Railway backend
exports.handler = async (event, context) => {
  const { path, httpMethod, headers, body } = event;
  
  // Remove /api from the path since our backend expects it
  const backendPath = path.replace('/.netlify/functions/api', '/api');
  const backendUrl = `https://wolfhunt-production.up.railway.app${backendPath}`;
  
  console.log(`Proxying ${httpMethod} ${path} to ${backendUrl}`);
  
  try {
    const response = await fetch(backendUrl, {
      method: httpMethod,
      headers: {
        ...headers,
        'host': undefined, // Remove host header to avoid conflicts
      },
      body: httpMethod !== 'GET' && httpMethod !== 'HEAD' ? body : undefined,
    });
    
    const responseBody = await response.text();
    
    return {
      statusCode: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Content-Type': response.headers.get('content-type') || 'application/json',
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
      body: JSON.stringify({ error: 'Proxy failed', details: error.message }),
    };
  }
};