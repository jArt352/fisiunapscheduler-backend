



from rest_framework.routers import DefaultRouter
from api.views import PersonCreateViewSet, GroupViewSet, AuthViewSet, JWTAuthViewSet, PlanImportViewSet, PlanListViewSet, SchoolViewSet, CourseUpdateViewSet, CourseViewSet, PlanAdminViewSet, AcademicPeriodCreateViewSet, AcademicPeriodListViewSet, AcademicPeriodUpdateViewSet, ShiftViewSet, CourseOfferingListViewSet, CourseOfferingGroupUpdateViewSet, CourseOfferingDetailViewSet, CourseGroupListViewSet
from api.views.CourseOfferingManualAddViewSet import CourseOfferingManualAddViewSet
from api.views.CourseGroupConfigViewSet import CourseGroupConfigViewSet
from api.views.CourseGroupBulkCreateViewSet import CourseGroupBulkCreateViewSet

router = DefaultRouter()
router.register(r'persons/create', PersonCreateViewSet, basename='person-create')
router.register(r'groups', GroupViewSet, basename='groups')
# Nuevo endpoint para agregar cursos manualmente a CourseOffering
router.register(r'course-offerings-manual-add', CourseOfferingManualAddViewSet, basename='course-offerings-manual-add')
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
router.register(r'shifts', ShiftViewSet, basename='shifts')
router.register(r'course-offerings', CourseOfferingListViewSet, basename='course-offerings')
router.register(r'course-offerings/groups', CourseOfferingGroupUpdateViewSet, basename='course-offerings-groups')
router.register(r'course-offerings/detail', CourseOfferingDetailViewSet, basename='course-offerings-detail')
router.register(r'course-groups', CourseGroupListViewSet, basename='course-groups')
router.register(r'course-group-configs', CourseGroupConfigViewSet, basename='course-group-configs')
router.register(r'course-groups-bulk', CourseGroupBulkCreateViewSet, basename='course-groups-bulk')

# Endpoint para agregar manualmente CourseOffering de tipo 'normal' y establecer número de grupos, curso por curso
from api.views.CourseOfferingManualNormalWithGroupsSingleViewSet import CourseOfferingManualNormalWithGroupsSingleViewSet
router.register(r'course-offerings-manual-normal-with-groups-single', CourseOfferingManualNormalWithGroupsSingleViewSet, basename='course-offerings-manual-normal-with-groups-single')

# Endpoint para agregar manualmente CourseOffering de tipo 'normal' y establecer número de grupos
from api.views.CourseOfferingManualNormalWithGroupsViewSet import CourseOfferingManualNormalWithGroupsViewSet
router.register(r'course-offerings-manual-normal-with-groups', CourseOfferingManualNormalWithGroupsViewSet, basename='course-offerings-manual-normal-with-groups')

# Endpoint para agregar manualmente CourseOffering de tipo 'normal'
from api.views.CourseOfferingManualNormalViewSet import CourseOfferingManualNormalViewSet
router.register(r'course-offerings-manual-normal', CourseOfferingManualNormalViewSet, basename='course-offerings-manual-normal')

# Endpoint para abrir cursos y establecer número de grupos en un solo paso
from api.views.CourseOfferingWithGroupsViewSet import CourseOfferingWithGroupsViewSet
router.register(r'course-offerings-with-groups', CourseOfferingWithGroupsViewSet, basename='course-offerings-with-groups')

# Endpoint para listar cursos que no abrieron en tipo 'normal'
from api.views.CoursesNotOpenedNormalViewSet import CoursesNotOpenedNormalViewSet
router.register(r'courses-not-opened-normal', CoursesNotOpenedNormalViewSet, basename='courses-not-opened-normal')
