from resource_logging.resource_service import ResourceLoggerService

logger = ResourceLoggerService(interval_sec=5)

logger.start()

try:

    while True:
        pass

except KeyboardInterrupt:

    logger.stop()