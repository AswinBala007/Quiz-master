<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1>Login to Quiz Master</h1>
      <div v-if="error" class="error-message">{{ error }}</div>
      <form @submit.prevent="login">
        <div class="form-group">
          <label for="email">Email</label>
          <input 
            type="email" 
            id="email" 
            v-model="email" 
            required
            placeholder="Enter your email"
          />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input 
            type="password" 
            id="password" 
            v-model="password" 
            required
            placeholder="Enter your password"
          />
        </div>
        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </div>
      </form>
      <div class="auth-footer">
        Don't have an account? 
        <router-link to="/register">Register</router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginPage',
  data() {
    return {
      email: '',
      password: '',
      error: '',
      loading: false
    }
  },
  methods: {
    async login() {
      this.loading = true
      this.error = ''
      
      try {
        const response = await this.$axios.post('/login', {
          email: this.email,
          password: this.password
        })
        
        // Store token
        localStorage.setItem('token', response.data.access_token)
        
        
        const userResponse = await this.$axios.get('/me', {
          headers: {
            Authorization: `Bearer ${response.data.access_token}`
          }
        })
        const userRole = userResponse.data.role || 'user'
        // Store role
        localStorage.setItem('userRole', userRole)
        
        // Redirect based on role
        if (userRole === 'admin') {
          this.$router.push('/admin')
        } else {
          this.$router.push('/dashboard')
        }
      } catch (error) {
        if (error.response) {
          this.error = error.response.data.message || 'Invalid login credentials'
        } else {
          this.error = 'An error occurred. Please try again.'
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  background-color: white;
}

h1 {
  margin-top: 0;
  text-align: center;
  color: #2c3e50;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #333;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-actions {
  margin-top: 1.5rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #3aa876;
}

.btn-primary:disabled {
  background-color: #93d7be;
  cursor: not-allowed;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.auth-footer {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
}

.auth-footer a {
  color: #42b983;
  text-decoration: none;
}
</style> 