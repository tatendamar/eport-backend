"""
Placeholder module. Templates have been moved to app/templates/*.html.
Remove imports of this module and use Jinja2Templates with the files in app/templates.
"""

__all__ = ["DEPRECATED_PLACEHOLDER"]

DEPRECATED_PLACEHOLDER = True
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/web/dashboard" class="text-xl font-bold text-gray-800">Warranty Register</a>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-gray-600">{{ user.email }}</span>
                    <a href="/web/logout" class="text-red-600 hover:text-red-800">Logout</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-xl mx-auto py-6 px-4">
        <div class="mb-6">
            <a href="/web/warranty/{{ warranty.id }}" class="text-blue-600 hover:underline">&larr; Back to Warranty Details</a>
        </div>

        <div class="bg-white shadow-md rounded-lg p-6">
            <h2 class="text-xl font-bold text-gray-800 mb-2">Update Warranty Status</h2>
            <p class="text-gray-600 mb-6">Asset: <strong>{{ warranty.asset_name }}</strong></p>

            {% if message %}
            <div class="mb-4 px-4 py-3 rounded {% if success %}bg-green-100 border border-green-400 text-green-700{% else %}bg-red-100 border border-red-400 text-red-700{% endif %}">
                {{ message }}
            </div>
            {% endif %}

            <div class="mb-6">
                <p class="text-gray-500">Current Status:</p>
                <span class="px-3 py-1 text-sm font-semibold rounded-full 
                    {% if warranty.warranty_status.value == 'registered' %}bg-green-100 text-green-800
                    {% elif warranty.warranty_status.value == 'active' %}bg-blue-100 text-blue-800
                    {% elif warranty.warranty_status.value == 'expired' %}bg-red-100 text-red-800
                    {% elif warranty.warranty_status.value == 'claimed' %}bg-purple-100 text-purple-800
                    {% else %}bg-gray-100 text-gray-800{% endif %}">
                    {{ warranty.warranty_status.value | capitalize }}
                </span>
            </div>

            <form method="POST" action="/web/warranty/{{ warranty.id }}/status">
                <div class="mb-6">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="new_status">
                        New Status
                    </label>
                    <select 
                        id="new_status" 
                        name="new_status" 
                        class="shadow border rounded w-full py-2 px-3 text-gray-700 focus:outline-none focus:shadow-outline"
                        required
                    >
                        <option value="">-- Select Status --</option>
                        <option value="registered" {% if warranty.warranty_status.value == 'registered' %}selected{% endif %}>Registered</option>
                        <option value="active" {% if warranty.warranty_status.value == 'active' %}selected{% endif %}>Active</option>
                        <option value="expired" {% if warranty.warranty_status.value == 'expired' %}selected{% endif %}>Expired</option>
                        <option value="claimed" {% if warranty.warranty_status.value == 'claimed' %}selected{% endif %}>Claimed</option>
                    </select>
                </div>

                <div class="flex space-x-3">
                    <button 
                        type="submit" 
                        class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:shadow-outline"
                    >
                        Update Status
                    </button>
                    <a href="/web/warranty/{{ warranty.id }}" 
                       class="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400">
                        Cancel
                    </a>
                </div>
            </form>
        </div>
    </main>
</body>
</html>
"""

CHECK_ASSET_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Check Asset Warranty</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/web/dashboard" class="text-xl font-bold text-gray-800">Warranty Register</a>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-gray-600">{{ user.email }}</span>
                    <a href="/web/logout" class="text-red-600 hover:text-red-800">Logout</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-xl mx-auto py-6 px-4">
        <div class="mb-6">
            <a href="/web/dashboard" class="text-blue-600 hover:underline">&larr; Back to Dashboard</a>
        </div>

        <div class="bg-white shadow-md rounded-lg p-6">
            <h2 class="text-xl font-bold text-gray-800 mb-2">Check Asset Warranty</h2>
            <p class="text-gray-600 mb-6">Enter an Asset ID to check if it has a registered warranty.</p>

            {% if message %}
            <div class="mb-4 px-4 py-3 rounded {% if found %}bg-green-100 border border-green-400 text-green-700{% else %}bg-yellow-100 border border-yellow-400 text-yellow-700{% endif %}">
                {{ message }}
            </div>
            {% endif %}

            {% if error %}
            <div class="mb-4 px-4 py-3 rounded bg-red-100 border border-red-400 text-red-700">
                {{ error }}
            </div>
            {% endif %}

            <form method="POST" action="/web/check-asset">
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="asset_id">
                        Asset ID (UUID)
                    </label>
                    <input 
                        type="text" 
                        id="asset_id" 
                        name="asset_id" 
                        value="{{ asset_id or '' }}"
                        placeholder="e.g., 123e4567-e89b-12d3-a456-426614174000"
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 focus:outline-none focus:shadow-outline font-mono text-sm"
                        required
                    >
                </div>

                <div class="mb-6">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="api_key">
                        API Key
                    </label>
                    <input 
                        type="password" 
                        id="api_key" 
                        name="api_key" 
                        placeholder="Enter your API key"
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 focus:outline-none focus:shadow-outline"
                        required
                    >
                    <p class="text-gray-500 text-xs mt-1">This endpoint requires API key authentication.</p>
                </div>

                <button 
                    type="submit" 
                    class="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:shadow-outline"
                >
                    Check Warranty
                </button>
            </form>

            {% if warranty %}
            <div class="mt-6 pt-6 border-t">
                <h3 class="text-lg font-semibold text-gray-700 mb-3">Warranty Found</h3>
                <dl class="space-y-2">
                    <div class="flex">
                        <dt class="w-32 text-gray-500">Asset Name:</dt>
                        <dd class="text-gray-900">{{ warranty.asset_name }}</dd>
                    </div>
                    <div class="flex">
                        <dt class="w-32 text-gray-500">Status:</dt>
                        <dd>
                            <span class="px-2 py-1 text-xs font-semibold rounded-full 
                                {% if warranty.warranty_status.value == 'registered' %}bg-green-100 text-green-800
                                {% elif warranty.warranty_status.value == 'active' %}bg-blue-100 text-blue-800
                                {% elif warranty.warranty_status.value == 'expired' %}bg-red-100 text-red-800
                                {% elif warranty.warranty_status.value == 'claimed' %}bg-purple-100 text-purple-800
                                {% else %}bg-gray-100 text-gray-800{% endif %}">
                                {{ warranty.warranty_status.value | capitalize }}
                            </span>
                        </dd>
                    </div>
                    <div class="flex">
                        <dt class="w-32 text-gray-500">End Date:</dt>
                        <dd class="text-gray-900">{% if warranty.warranty_end_date %}{{ warranty.warranty_end_date.strftime('%Y-%m-%d') }}{% else %}-{% endif %}</dd>
                    </div>
                </dl>
                <a href="/web/warranty/{{ warranty.id }}" 
                   class="mt-4 inline-block px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                    View Full Details
                </a>
            </div>
            {% endif %}
        </div>
    </main>
</body>
</html>
"""
