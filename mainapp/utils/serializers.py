from rest_framework import serializers


class DynamicFieldsBaseModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes additional `fields`, `exclude`, `read_only_fields`,
    and `extra_kwargs` arguments to control which fields are displayed and how.
    """

    def __init__(self, *args, **kwargs):
        # Extract dynamic arguments, provide defaults if not passed
        fields = kwargs.pop('fields', getattr(self.Meta, 'fields', None))
        
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        # Handle field inclusion/exclusion after instantiating parent class
        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
