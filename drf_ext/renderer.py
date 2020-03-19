"""
========
Renderer
========
Change the framework's standard response structure to Woodenpineapple specific response.

The response design is follow

For single object or data::


    {
        "data": {
        }
    }

For list of object::

    {
        "meta": {
            "count": "TOTAL RECORD COUNT"
            "next": "NEXT PAGE LINK"
            "previous": "PREVIOUS PAGE LINK"
        },
        "data": [
        ]
    }

When error occurs::

    {
        "error": {
            "type": "ERROR TYPE",
            "detail": "HUMAN READABLE MESSAGE",
            "status_code": "APPROPRIATE STATUS CODE",
            "error_code": "ERROR CODE"

        }
    }
"""
from rest_framework.renderers import JSONRenderer as RFJSONRenderer


class JSONRenderer(RFJSONRenderer):
    """
    Override the ``render()`` of the rest framework JSONRenderer to produce JSON output as per \
    API specification
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        from . import utils
        
        response_data = {}
        context = 'data'  # Default

        # When exception handler will pass the response, we would expect
        # the context to be `error`
        if isinstance(data, dict) and data.get('_context') == 'error':
            context = 'error'
            data.pop('_context', None)

            # Normalizing detail field in error, only first element of dict should be visible
            if data.get('non_field_errors'):
                data['detail'] = data.pop('non_field_errors')[0]
            elif data.get('detail'):
                pass
            else:
                detail = None
                data_flatten = utils.flatten_dict(data.copy())
                for k, v in data_flatten.copy().items():
                    if k in ['type', 'error_code', 'status_code']:
                        continue

                    err_list = data_flatten.pop(k)
                    k = k.split('.')[-1]  # last dict's key

                    if isinstance(err_list, list):
                        detail = err_list[0].replace(
                            'This field', '`%s`' % utils.snake_case_to_title(k)
                        ).replace(
                            'This list', '`%s`' % utils.snake_case_to_title(k)
                        )

                data_flatten['detail'] = detail
                data = data_flatten

        # check if the results have been paginated
        if isinstance(data, dict) and 'results' in data:
            # add the resource key and copy the results
            response_data[context] = data.pop('results')
            response_data['meta'] = data
        else:
            response_data[context] = data

        # call super to render the response
        response = super().render(response_data, accepted_media_type, renderer_context)

        return response
