from fabrick import Fabrick, start, step, finish, ON

@start
def function_a(context):
    return {
        "status": "success",
        "data": {"raw_input": context.input},
        "next_state": "function_b",
        "metadata": {}
    }

@step
def function_b(context):
    return {
        "status": "success",
        "data": {"processed": True},
        "next_state": "function_c",
        "metadata": {}
    }

@step
def function_c(context):
    return {
        "status": "success",
        "data": {"decision": "ok"},
        "next_state": "function_d",
        "metadata": {}
    }

@finish
def function_d(context):
    return {
        "status": "success",
        "data": {"result": "done"},
        "metadata": {}
    }


workflow = Fabrick(
    name="Pipeline de IA",
    scheduler="0 12 * * *",          # cron
    start_at="2026-02-15",
    retry=ON,
    execution_mode="background",    # local | background | queue | cloud
    persistence="postgres",          # sqlite | postgres | redis
    observability="langsmith"
)

workflow.register(function_a, function_b, function_c, function_d)
workflow.run()
