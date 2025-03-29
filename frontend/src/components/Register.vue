<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1>Register for Quiz Master</h1>
      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-if="success" class="success-message">{{ success }}</div>
      <form @submit.prevent="register">
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
          <label for="fullname">Full Name</label>
          <input 
            type="text" 
            id="fullname" 
            v-model="fullName" 
            required
            placeholder="Enter your full name"
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
        <div class="form-group">
          <label for="qualification">Qualification (Optional)</label>
          <input 
            type="text" 
            id="qualification" 
            v-model="qualification" 
            placeholder="Enter your qualification"
          />
        </div>
        <div class="form-group">
          <label for="dob">Date of Birth (DD/MM/YYYY)</label>
          <input 
            type="text" 
            id="dob" 
            v-model="dob" 
            placeholder="DD/MM/YYYY"
          />
        </div>
        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Registering...' : 'Register' }}
          </button>
        </div>
      </form>
      <div class="auth-footer">
        Already have an account? 
        <router-link to="/login">Login</router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RegisterPage',
  data() {
    return {
      email: '',
      fullName: '',
      password: '',
      qualification: '',
      dob: '',
      error: '',
      success: '',
      loading: false
    }
  },
  methods: {
    async register() {
      this.loading = true
      this.error = ''
      this.success = ''
      
      try {
        await this.$axios.post('/register', {
          email: this.email,
          full_name: this.fullName,
          password: this.password,
          qualification: this.qualification || null,
          dob: this.dob || null
        })
        
        this.success = 'Registration successful! You can now login.'
        
        // Clear form
        this.email = ''
        this.fullName = ''
        this.password = ''
        this.qualification = ''
        this.dob = ''
        
        // Redirect to login after 2 seconds
        setTimeout(() => {
          this.$router.push('/login')
        }, 2000)
      } catch (error) {
        if (error.response) {
          this.error = error.response.data.message || 'Registration failed'
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
  padding: 2rem 0;
}

.auth-card {
  width: 100%;
  max-width: 450px;
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

.success-message {
  background-color: #d4edda;
  color: #155724;
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