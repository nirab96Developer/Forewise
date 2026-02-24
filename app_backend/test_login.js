const axios = require('axios');

async function testLogin() {
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/v1/auth/login', {
      email: 'admin@kkl.co.il',
      password: 'admin123'
    });
    console.log('✅ Login successful:', response.data);
  } catch (error) {
    console.log('❌ Login failed:', error.response?.data || error.message);
  }
}

testLogin();





