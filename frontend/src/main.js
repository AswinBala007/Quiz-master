import axios from 'axios'
import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import components for routing
import Dashboard from './components/Dashboard.vue'
import Login from './components/Login.vue'
import QuizAttempt from './components/QuizAttempt.vue'
import QuizList from './components/QuizList.vue'
import Register from './components/Register.vue'
import SubjectList from './components/SubjectList.vue'
import UserHistory from './components/UserHistory.vue'
import UserProfile from './components/UserProfile.vue'

// Import admin components
import AdminChapters from './components/admin/AdminChapters.vue'
import AdminDashboard from './components/admin/AdminDashboard.vue'
import AdminQuestions from './components/admin/AdminQuestions.vue'
import AdminQuizzes from './components/admin/AdminQuizzes.vue'
import AdminSubjects from './components/admin/AdminSubjects.vue'
import AdminUsers from './components/admin/AdminUsers.vue'

// Create routes
const routes = [
    { path: '/', redirect: '/login' },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    {
        path: '/dashboard',
        component: Dashboard,
        meta: { requiresAuth: true }
    },
    {
        path: '/subjects',
        component: SubjectList,
        meta: { requiresAuth: true }
    },
    {
        path: '/quizzes/:subjectId',
        component: QuizList,
        meta: { requiresAuth: true }
    },
    {
        path: '/quiz/:quizId',
        component: QuizAttempt,
        meta: { requiresAuth: true }
    },
    {
        path: '/profile',
        component: UserProfile,
        meta: { requiresAuth: true }
    },
    {
        path: '/history',
        component: UserHistory,
        meta: { requiresAuth: true }
    },
    // Admin routes
    {
        path: '/admin',
        component: AdminDashboard,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/admin/subjects',
        component: AdminSubjects,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/admin/subjects/:subjectId/chapters',
        component: AdminChapters,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/admin/chapters/:chapterId/quizzes',
        component: AdminQuizzes,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/admin/quizzes/:quizId/questions',
        component: AdminQuestions,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/admin/users',
        component: AdminUsers,
        meta: { requiresAuth: true, requiresAdmin: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Set up API base URL
axios.defaults.baseURL = 'http://localhost:5000'

// Add auth token to requests
axios.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Navigation guard
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    const userRole = localStorage.getItem('userRole')

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!token) {
            next('/login')
        } else if (to.matched.some(record => record.meta.requiresAdmin) && userRole !== 'admin') {
            // Redirect to user dashboard if trying to access admin routes without admin role
            next('/dashboard')
        } else {
            next()
        }
    } else {
        next()
    }
})

const app = createApp(App)
app.use(router)

// Make axios available throughout the app
app.config.globalProperties.$axios = axios

app.mount('#app')
