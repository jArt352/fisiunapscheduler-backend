from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from api.models import Person, Teacher, SchoolDirector, DepartmentHead, School, Faculty


class PersonCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    roles = serializers.ListField(child=serializers.IntegerField(), required=False)
    # role-specific nested data accepted as JSON objects (allow lists, nulls, ints)
    teacher = serializers.JSONField(required=False)
    school_director = serializers.JSONField(required=False)
    department_head = serializers.JSONField(required=False)
    # allow phone to be blank in input
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Person
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'profile_image', 'dni', 'email', 'phone', 'username', 'password', 'roles', 'teacher', 'school_director', 'department_head']
        read_only_fields = ['id']

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        if username and not password:
            raise serializers.ValidationError("Si proporciona username, también debe proporcionar password.")
        return data

    def create(self, validated_data):
        from django.db import transaction
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        roles = validated_data.pop('roles', [])
        teacher_data = validated_data.pop('teacher', {})
        school_director_data = validated_data.pop('school_director', {})
        department_head_data = validated_data.pop('department_head', {})
        User = get_user_model()

        with transaction.atomic():
            user = None
            if username:
                if User.objects.filter(username=username).exists():
                    raise serializers.ValidationError({'username': 'Ya existe un usuario con ese username.'})
                user = User.objects.create_user(username=username, password=password)

            person = Person.objects.create(**validated_data)

            if user:
                person.user = user
                person.save()

            # Assign roles: accept list of group ids
            groups = []
            for r in roles:
                try:
                    gid = int(r)
                except Exception:
                    raise serializers.ValidationError({'roles': 'Cada rol debe enviarse como el id numérico del Group.'})

                try:
                    g = Group.objects.get(pk=gid)
                except Group.DoesNotExist:
                    raise serializers.ValidationError({'roles': f'Grupo con id {gid} no existe.'})

                groups.append(g)

            if groups:
                person.roles.set(groups)

            # Create related role entities if roles include them
            role_names = {g.name for g in groups}

            # Teacher
            if 'teacher' in role_names:
                # required fields: contract_type, min_weekly_hours (optional: max_unavailability_hours)
                contract_type = teacher_data.get('contract_type') or teacher_data.get('contract')
                min_hours = teacher_data.get('min_weekly_hours') or teacher_data.get('min_hours')
                max_unavail = teacher_data.get('max_unavailability_hours') or teacher_data.get('max_unavail')
                # coerce to ints when possible
                try:
                    min_hours = int(min_hours) if min_hours is not None else 0
                except Exception:
                    raise serializers.ValidationError({'teacher': 'min_weekly_hours debe ser un entero.'})
                try:
                    max_unavail = int(max_unavail) if max_unavail is not None else 0
                except Exception:
                    raise serializers.ValidationError({'teacher': 'max_unavailability_hours debe ser un entero.'})

                teacher_obj = Teacher.objects.create(person=person, contract_type=contract_type or 'contratado', min_weekly_hours=min_hours, max_unavailability_hours=max_unavail)

                # assign faculties if provided (list of ids or names)
                facs = teacher_data.get('faculties') or teacher_data.get('faculties_ids') or teacher_data.get('faculties_list')
                if facs:
                    faculty_objs = []
                    for f in facs:
                        try:
                            fid = int(f)
                        except Exception:
                            raise serializers.ValidationError({'teacher': 'Cada faculty debe enviarse como id numérico.'})

                        try:
                            fac = Faculty.objects.get(pk=fid)
                        except Faculty.DoesNotExist:
                            raise serializers.ValidationError({'teacher': f'Faculty con id {fid} no existe.'})

                        faculty_objs.append(fac)

                    if faculty_objs:
                        teacher_obj.faculties.set(faculty_objs)

            # School director
            if 'school_director' in role_names:
                school_id = school_director_data.get('school_id') or school_director_data.get('school')
                start_date = school_director_data.get('start_date')
                end_date = school_director_data.get('end_date')
                if not school_id:
                    raise serializers.ValidationError({'school_director': 'Se debe proporcionar school_id para director de escuela.'})
                try:
                    school = School.objects.get(pk=int(school_id))
                except Exception:
                    raise serializers.ValidationError({'school_director': f'School con id {school_id} no existe.'})
                SchoolDirector.objects.create(school=school, person=person, start_date=start_date or None, end_date=end_date or None)

            # Department head
            if 'department_chief' in role_names or 'department_head' in role_names:
                school_id = department_head_data.get('school_id') or department_head_data.get('school')
                dept_name = department_head_data.get('department_name') or department_head_data.get('department')
                start_date = department_head_data.get('start_date')
                end_date = department_head_data.get('end_date')
                if not school_id or not dept_name:
                    raise serializers.ValidationError({'department_head': 'Se requieren school_id y department_name para jefe de departamento.'})
                try:
                    school = School.objects.get(pk=int(school_id))
                except Exception:
                    raise serializers.ValidationError({'department_head': f'School con id {school_id} no existe.'})
                DepartmentHead.objects.create(school=school, person=person, department_name=dept_name, start_date=start_date or None, end_date=end_date or None)

            return person
