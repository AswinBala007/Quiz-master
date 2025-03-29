<template>
  <div class="subject-container">
    <UserNavBar />
    <h1>Subjects</h1>
    <div v-if="loading" class="loading-indicator">Loading subjects...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <div v-else-if="subjects.length === 0" class="empty-state">
      <div class="empty-icon">📚</div>
      <h3>No subjects available</h3>
      <p>There are currently no subjects available. Please check back later.</p>
    </div>
    <div v-else class="subject-grid">
      <div 
        v-for="subject in subjects" 
        :key="subject.id" 
        class="subject-card"
        @click="navigateToQuizzes(subject.id)"
      >
        <div class="subject-name">{{ subject.name }}</div>
        <div class="subject-action">View Quizzes &rarr;</div>
      </div>
    </div>
  </div>
</template>

<script>
import UserNavBar from './UserNavBar.vue'
export default {
  name: 'SubjectList',
  components: {
    UserNavBar
  },
  data() {
    return {
      subjects: [],
      loading: true,
      error: null
    }
  },
  async created() {
    await this.fetchSubjects()
  },
  methods: {
    async fetchSubjects() {
      try {
        const response = await this.$axios.get('/user/subjects')
        this.subjects = response.data
      } catch (error) {
        this.error = 'Failed to load subjects. Please try again later.'
        console.error('Error fetching subjects:', error)
        
        if (error.response && error.response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token')
          this.$router.push('/login')
        }
      } finally {
        this.loading = false
      }
    },
    navigateToQuizzes(subjectId) {
      this.$router.push(`/quizzes/${subjectId}`)
    }
  }
}
</script>

<style scoped>
.subject-container {
  padding: 1rem;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.subject-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.subject-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  display: flex;
  flex-direction: column;
}

.subject-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.subject-name {
  font-size: 1.25rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.subject-action {
  margin-top: auto;
  color: #42b983;
  font-weight: bold;
  text-align: right;
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
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.empty-state p {
  color: #666;
  max-width: 400px;
  margin: 0 auto;
}
</style> 