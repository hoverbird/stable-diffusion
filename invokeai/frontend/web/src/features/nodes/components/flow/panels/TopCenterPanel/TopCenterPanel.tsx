import { Flex } from '@chakra-ui/layout';
import { memo } from 'react';
import LoadWorkflowButton from './LoadWorkflowButton';
import ResetWorkflowButton from './ResetWorkflowButton';
import SaveWorkflowButton from './SaveWorkflowButton';

const TopCenterPanel = () => {
  return (
    <Flex
      sx={{
        gap: 2,
        position: 'absolute',
        top: 2,
        insetInlineStart: '50%',
        transform: 'translate(-50%)',
      }}
    >
      <SaveWorkflowButton />
      <LoadWorkflowButton />
      <ResetWorkflowButton />
    </Flex>
  );
};

export default memo(TopCenterPanel);
