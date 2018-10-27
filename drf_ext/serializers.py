"""
===========
Serializers
===========
"""
from rest_framework import serializers as rf_serializers


class Serializer(rf_serializers.Serializer):
    """
    Base serializer that adds a feature of dynamically allow selection fields in response.
    """

    def __init__(self, *args, **kwargs):
        _fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        # Dynamically allow selection of fields
        try:
            fields = self.context.get('request').GET.get('fields')
        except AttributeError:
            fields = _fields
        if fields:
            if isinstance(fields, str):
                fields = fields.split(',')
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ModelSerializer(rf_serializers.ModelSerializer, Serializer):
    """
    Base serializer for model
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meta = getattr(self, 'Meta', None)

        # Update the error messages specified under the Meta class for each fields
        for field_name, err_msgs in getattr(meta, 'error_messages', {}).items():
            try:
                self.fields[field_name].error_messages.update(**err_msgs)
            except KeyError:
                pass

    @property
    def validated_data(self):
        """
        Overridden method to inject logged in user object to validated_data dict
        """
        validated_data = super().validated_data
        owner_field = getattr(self.Meta, 'owner_field', None)

        if owner_field:
            validated_data[owner_field] = self.context['request'].user

        return validated_data

    def update(self, instance, validated_data):
        # Exclude those fields defined under Meta.exclude_on_update attribute
        exclude_on_update = getattr(self.Meta, 'exclude_on_update', [])
        for field in exclude_on_update:
            validated_data.pop(field, None)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Overridden method to filter private fields
        """
        return self.__filter_private_fields(super().to_representation(instance), instance)

    def __filter_private_fields(self, data, instance):
        """
        Filters data dict to remove private fields from other users excluding staff and admin

        :param dict data: Returned from to_representation()
        :param instance: Instance where owner field will be looked up
        :return dict: Filtered dict
        """
        try:
            user = self.context['request'].user
        except (KeyError, AttributeError):
            return data

        private_fields = getattr(self.Meta, 'private_fields', None)
        if not private_fields:
            return data

        is_owner = False
        if getattr(self.Meta, 'owner_field', None):
            is_owner = getattr(instance, self.Meta.owner_field) == user

        for k in list(data.keys()):
            if k in private_fields and not user.is_superuser and not user.is_staff and not is_owner:
                data.pop(k, None)

        return data
