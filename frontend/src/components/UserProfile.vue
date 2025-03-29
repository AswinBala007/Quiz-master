<template>
  <!-- <AdminNavBar v-if="user && user.role == 'admin'" /> -->
  
  <div class="profile-container">
    <!-- <AdminNavBar v-if="localStorage.getItem('userRole') == 'admin'" />
    <UserNavBar v-else-if="localStorage.getItem('userRole') == 'user'" /> -->
    <h1>User Profile</h1>
    
    <div v-if="loading" class="loading-indicator">Loading profile...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else class="profile-content">
      <!-- Profile Information Card -->
      <div class="profile-card">
        <div class="profile-header">
          <div class="profile-avatar">{{ initials }}</div>
          <div>
            <h2>{{ user.full_name }}</h2>
            <div class="profile-email">{{ user.email }}</div>
          </div>
        </div>
        
        <div class="profile-info">
          <div class="info-row">
            <div class="info-label">Role:</div>
            <div class="info-value">{{ capitalizeRole(user.role) }}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">Account Created:</div>
            <div class="info-value">{{ formatDate(user.created_at) }}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">Last Login:</div>
            <div class="info-value">{{ formatDate(user.last_login) }}</div>
          </div>
        </div>
      </div>
      
      <!-- Profile Edit Form -->
      <div class="profile-card">
        <h3>Edit Profile</h3>
        <div v-if="updateSuccess" class="success-message">Profile updated successfully!</div>
        <div v-if="updateError" class="error-message">{{ updateError }}</div>
        
        <form @submit.prevent="updateProfile">
          <div class="form-group">
            <label for="fullName">Full Name</label>
            <input 
              type="text" 
              id="fullName" 
              v-model="form.fullName" 
              required
            />
          </div>
          
          <div class="form-group">
            <label for="qualification">Qualification</label>
            <input 
              type="text" 
              id="qualification" 
              v-model="form.qualification" 
              placeholder="Your qualification (optional)"
            />
          </div>
          
          <div class="form-group">
            <label for="dob">Date of Birth (DD/MM/YYYY)</label>
            <input 
              type="text" 
              id="dob" 
              v-model="form.dob" 
              placeholder="DD/MM/YYYY"
            />
          </div>
          
          <div class="form-actions">
            <button type="submit" class="btn-update" :disabled="updating">
              {{ updating ? 'Updating...' : 'Update Profile' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserProfile',
  data() {
    return {
      user: {},
      loading: true,
      error: null,
      updateError: null,
      updateSuccess: false,
      updating: false,
      form: {
        fullName: '',
        qualification: '',
        dob: ''
      }
    }
  },
  computed: {
    initials() {
      if (!this.user.full_name) return '?'
      
      return this.user.full_name
        .split(' ')
        .map(name => name[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
  },
  async created() {
    await this.fetchUserData()
  },
  methods: {
    async fetchUserData() {
      try {
        const response = await this.$axios.get('/me')
        this.user = response.data
        
        // Populate form with current data
        this.form.fullName = this.user.full_name
        this.form.qualification = this.user.qualification || ''
        this.form.dob = this.user.dob || ''
      } catch (error) {
        this.error = 'Failed to load profile data'
        console.error(error)
        
        if (error.response && error.response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token')
          this.$router.push('/login')
        }
      } finally {
        this.loading = false
      }
    },
    
    async updateProfile() {
      this.updating = true
      this.updateError = null
      this.updateSuccess = false
      
      try {
        await this.$axios.put('/profile', {
          full_name: this.form.fullName,
          qualification: this.form.qualification || null,
          dob: this.form.dob || null
        })
        
        // Update local data
        this.user.full_name = this.form.fullName
        this.user.qualification = this.form.qualification
        this.user.dob = this.form.dob
        
        this.updateSuccess = true
        
        // Hide success message after 3 seconds
        setTimeout(() => {
          this.updateSuccess = false
        }, 3000)
      } catch (error) {
        if (error.response) {
          this.updateError = error.response.data.message || 'Failed to update profile'
        } else {
          this.updateError = 'Connection error. Please try again later.'
        }
        console.error('Error updating profile:', error)
      } finally {
        this.updating = false
      }
    },
    
    capitalizeRole(role) {
      if (!role) return 'User'
      return role.charAt(0).toUpperCase() + role.slice(1)
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 1rem;
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 768px) {
  .profile-content {
    grid-template-columns: 1fr 1fr;
  }
}

.profile-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.profile-header {
  display: flex;
  align-items: center;
  margin-bottom: 1.5rem;
}

.profile-avatar {
  width: 60px;
  height: 60px;
  background-color: #42b983;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-right: 1rem;
}

h2 {
  margin: 0 0 0.25rem 0;
  color: #2c3e50;
}

.profile-email {
  color: #666;
  font-size: 0.9rem;
}

.profile-info {
  border-top: 1px solid #eee;
  padding-top: 1.5rem;
}

.info-row {
  display: flex;
  margin-bottom: 0.75rem;
}

.info-label {
  width: 40%;
  font-weight: bold;
  color: #555;
}

.info-value {
  width: 60%;
  color: #333;
}

/* Form Styles */
h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 1.25rem;
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

.btn-update {
  padding: 0.75rem 1.5rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-update:hover {
  background-color: #3aa876;
}

.btn-update:disabled {
  background-color: #93d7be;
  cursor: not-allowed;
}

.loading-indicator {
  text-align: center;
  font-size: 1.2rem;
  padding: 2rem;
  color: #666;
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
</style> 