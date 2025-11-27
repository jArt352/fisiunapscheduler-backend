from rest_framework.routers import DefaultRouter
from api.views import PersonCreateViewSet, GroupViewSet, AuthViewSet, JWTAuthViewSet, PlanImportViewSet, PlanListViewSet, SchoolViewSet, CourseUpdateViewSet, CourseViewSet, PlanAdminViewSet, AcademicPeriodCreateViewSet, AcademicPeriodListViewSet, AcademicPeriodUpdateViewSet

router = DefaultRouter()
router.register(r'persons/create', PersonCreateViewSet, basename='person-create')
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'auth', AuthViewSet, basename='auth')
# JWT auth (login -> sets refresh cookie, refresh -> uses cookie, logout -> clears cookie)
router.register(r'jwt', JWTAuthViewSet, basename='jwt-auth')
router.register(r'plans/import', PlanImportViewSet, basename='plans-import')
router.register(r'plans-list/full', PlanListViewSet, basename='plans-list-full')
router.register(r'schools', SchoolViewSet, basename='schools')
router.register(r'courses/update', CourseUpdateViewSet, basename='courses-update')
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'plans-admin', PlanAdminViewSet, basename='plans-admin')
router.register(r'academic-periods/create', AcademicPeriodCreateViewSet, basename='academic-periods-create')
router.register(r'academic-periods', AcademicPeriodListViewSet, basename='academic-periods')
router.register(r'academic-periods/update', AcademicPeriodUpdateViewSet, basename='academic-periods-update')
