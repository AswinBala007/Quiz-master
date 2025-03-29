<template>
  <header class="admin-header">
    <nav>
      <div class="nav-brand">Quiz Master <span class="admin-indicator">Admin</span></div>
      <div class="nav-links">
        <router-link to="/admin">Dashboard</router-link>
        <router-link to="/admin/subjects">Subjects</router-link>
        <router-link to="/admin/users">Users</router-link>
        <router-link to="/profile">Profile</router-link>
        <a @click.prevent="logout" class="logout-link">Logout</a>
        <!-- <div class="admin-badge">{{ user.full_name }}</div> -->
      </div>
    </nav>
  </header>
</template>

<script>
export default {
  name: 'AdminNavBar',
  // props: {
  //   user: {
  //     type: Object,
  //     default: null
  //   }
  // },
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
.admin-header {
  background-color: #343a40;
  color: white;
  padding: 0 1rem;
  border-bottom: 3px solid #dc3545;
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
  display: flex;
  align-items: center;
}

.admin-indicator {
  font-size: 0.7rem;
  background-color: #dc3545;
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  margin-left: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
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
  color: #f8f9fa;
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
  background: #dc3545;
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

.admin-badge {
  background-color: #dc3545;
  color: white;
  font-size: 0.8rem;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  margin-left: 1rem;
}
</style> 