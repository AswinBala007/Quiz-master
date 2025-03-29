<template>
  <header class="user-header">
    <nav>
      <div class="nav-brand">Quiz Master</div>
      <div class="nav-links">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link to="/subjects">Subjects</router-link>
        <router-link to="/history">History</router-link>
        <router-link to="/profile">Profile</router-link>
        <a href="#" @click.prevent="logout" class="logout-link">Logout</a>
        <div v-if="user" class="user-badge">{{ user.full_name }}</div>
      </div>
    </nav>
  </header>
</template>

<script>
export default {
  name: 'UserNavBar',
  props: {
    user: {
      type: Object,
      default: null
    }
  },
  methods: {
    logout() {
      // Clear authentication data
      localStorage.removeItem('token')
      localStorage.removeItem('userRole')
      
      // Redirect to login page
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.user-header {
  background-color: #2c3e50;
  color: white;
  padding: 0 1rem;
  border-bottom: 3px solid #42b983;
}

nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 0;
  position: relative;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #42b983;
}

/* Add underline animation for links */
.nav-links a:after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px;
  display: block;
  margin-top: 5px;
  left: 0;
  background: #42b983;
  transition: width 0.3s ease;
}

.nav-links a:hover:after,
.nav-links a.router-link-active:after {
  width: 100%;
}

.logout-link {
  margin-left: 1rem;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.1);
  transition: background-color 0.3s;
}

.logout-link:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.user-badge {
  background-color: #42b983;
  color: white;
  font-size: 0.8rem;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  margin-left: 1rem;
}
</style> 